import os
import re
import uuid
import traceback
from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename

# ✅ Add this missing import:
from dotenv import load_dotenv

# LangChain and Google AI
from langchain_community.document_loaders import PyPDFLoader, PDFPlumberLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# --- Environment Setup --

# Option 2: Load from .env (if preferred)
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Flask Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- App State ---
session_data = {}
user_retrievers = {}

# --- Load AI Models ---
llm, embeddings = None, None
if GOOGLE_API_KEY:
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.3, google_api_key=GOOGLE_API_KEY)
        print("✅ Google AI models loaded successfully.")
    except Exception as e:
        print(f"❌ Error loading models: {e}")
else:
    print("❌ GOOGLE_API_KEY not set. Please check your .env file.")

# --- Prompt ---
template = """
You are an AI assistant for the uploaded document(s). Use the following context to answer the question.
If you don't know the answer from the context, just say that you don't know.
Context: {context}
Question: {question}
Helpful Answer:"""
prompt = PromptTemplate.from_template(template)

# --- Utility ---
def parse_questions(response_content):
    questions = re.findall(r"^\d+\.\s.*", response_content, re.MULTILINE)
    return [re.sub(r"^\d+\.\s", "", q).strip() for q in questions]

# --- Session Handling ---
@app.before_request
def make_session_permanent():
    if 'id' not in session:
        session['id'] = str(uuid.uuid4())

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    session_id = session['id']
    if not embeddings:
        return jsonify({"success": False, "error": "Google AI models not loaded."}), 500

    if session_id not in session_data:
        session_data[session_id] = {'chunks': [], 'filenames': []}

    if len(session_data[session_id]['filenames']) >= 3:
        return jsonify({"success": False, "error": "You have already uploaded the maximum of 3 PDFs."}), 400

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({"success": False, "error": "Please select a valid PDF file"}), 400

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(filepath)

        # Try both loaders
        try:
            loader = PyPDFLoader(filepath)
            new_docs = loader.load()
        except Exception as e:
            print(f"⚠️ PyPDFLoader failed: {e}")
            loader = PDFPlumberLoader(filepath)
            new_docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        new_chunks = splitter.split_documents(new_docs)

        session_data[session_id]['chunks'].extend(new_chunks)
        session_data[session_id]['filenames'].append(filename)

        all_chunks = session_data[session_id]['chunks']
        vector_store = FAISS.from_documents(all_chunks, embeddings)
        user_retrievers[session_id] = vector_store.as_retriever()

        remaining = 3 - len(session_data[session_id]['filenames'])
        message = f"Added '{filename}'. You can add {remaining} more." if remaining else "Maximum of 3 PDFs added. You can now ask questions."

        print(f"✅ File '{filename}' uploaded and processed for session {session_id}")
        return jsonify({
            "success": True,
            "message": message,
            "uploaded_files": session_data[session_id]['filenames']
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": "Failed to process the PDF file."}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    session_id = session['id']
    if session_id not in user_retrievers or not llm:
        return jsonify({"error": "Please upload a document first or check your API key."}), 400

    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        retriever = user_retrievers[session_id]
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt}
        )
        result = qa_chain.invoke({"query": question})
        answer = result['result']

        follow_up_prompt = f"""Based on the last question and its answer, generate 3 new follow-up questions. Present them as a numbered list. Do not add any other text.
Last Question: "{question}"
Last Answer: "{answer}"
"""
        response = llm.invoke(follow_up_prompt)
        suggestions = parse_questions(response.content)

        return jsonify({"answer": answer, "suggestions": suggestions})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "An error occurred while generating the answer."}), 500

@app.route('/clear', methods=['POST'])
def clear_session():
    session_id = session['id']
    session_data.pop(session_id, None)
    user_retrievers.pop(session_id, None)
    print(f"🧹 Session cleared for {session_id}")
    return jsonify({"success": True, "message": "Session cleared."})

# --- Start ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)
