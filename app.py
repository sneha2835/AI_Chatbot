# app.py

import os
import re
import uuid
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Import LangChain components
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) 
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Global Objects & Model Loading ---
# NEW: Data structures to handle multiple files per session
session_data = {}  # Stores chunks and filenames: { 'session_id': {'chunks': [], 'filenames': []} }
user_retrievers = {} # Stores the final, searchable index: { 'session_id': retriever_object }

try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.3)
    template = """You are an AI assistant for the uploaded document(s). Use the following context to answer the question. If you don't know the answer from the context, just say that you don't know.
    Context: {context}
    Question: {question}
    Helpful Answer:"""
    prompt = PromptTemplate.from_template(template)
    print("AI Models loaded successfully.")
except Exception as e:
    print(f" Error loading AI models: {e}")
    llm = None

# --- Helper Function ---
def parse_questions(response_content):
    """Extracts questions from a numbered list string."""
    questions = re.findall(r"^\d+\.\s.*", response_content, re.MULTILINE)
    return [re.sub(r"^\d+\.\s", "", q).strip() for q in questions]

# --- Session Management ---
@app.before_request
def make_session_permanent():
    """Sets a unique ID for each user's session."""
    if 'id' not in session:
        session['id'] = str(uuid.uuid4())

# --- API Endpoints ---
@app.route('/')
def index():
    """Renders the main chat page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles PDF uploads, accumulates them, and enforces the 3-file limit."""
    session_id = session['id']
    if session_id not in session_data:
        session_data[session_id] = {'chunks': [], 'filenames': []}
    
    # --- ENFORCE 3 PDF LIMIT ---
    if len(session_data[session_id]['filenames']) >= 3:
        return jsonify({
            "success": False, 
            "error": "You have already uploaded the maximum of 3 PDFs."
        }), 400

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({"success": False, "error": "Please select a valid PDF file"}), 400

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(filepath)

        # Process the new PDF into chunks
        loader = PyPDFLoader(filepath)
        new_docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        new_chunks = text_splitter.split_documents(new_docs)

        # Accumulate chunks and filenames
        session_data[session_id]['chunks'].extend(new_chunks)
        session_data[session_id]['filenames'].append(filename)

        # Rebuild the retriever from ALL accumulated chunks
        all_chunks = session_data[session_id]['chunks']
        vector_store = FAISS.from_documents(all_chunks, embeddings)
        user_retrievers[session_id] = vector_store.as_retriever()
        
        remaining_slots = 3 - len(session_data[session_id]['filenames'])
        message = f"Added '{filename}'. You can add {remaining_slots} more."
        if remaining_slots == 0:
            message = "Maximum of 3 PDFs added. You can now start asking questions."

        print(f"File '{filename}' added for session {session_id}")
        return jsonify({
            "success": True, 
            "message": message,
            "uploaded_files": session_data[session_id]['filenames']
        })
    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({"success": False, "error": "Failed to process the PDF file."}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handles a user's question against the combined context of all uploaded PDFs."""
    session_id = session['id']
    if session_id not in user_retrievers:
        return jsonify({"error": "Please upload a document first."}), 400

    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        retriever = user_retrievers[session_id]
        qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, chain_type_kwargs={"prompt": prompt})
        result = qa_chain.invoke({"query": question})
        answer = result['result']
        
        # Generate follow-up suggestions
        follow_up_prompt = f"""Based on the last question and its answer, generate 3 new follow-up questions. Present them as a numbered list. Do not add any other text.
        Last Question: "{question}"
        Last Answer: "{answer}" """
        response = llm.invoke(follow_up_prompt)
        suggestions = parse_questions(response.content)

        return jsonify({"answer": answer, "suggestions": suggestions})
    except Exception as e:
        print(f" Error during QA: {e}")
        return jsonify({"error": "An error occurred while generating the answer."}), 500

@app.route('/clear', methods=['POST'])
def clear_session():
    """Clears all data for the user's session to let them start over."""
    session_id = session['id']
    session_data.pop(session_id, None)
    user_retrievers.pop(session_id, None)
    print(f"Session cleared for {session_id}")
    return jsonify({"success": True, "message": "Session cleared."})

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)