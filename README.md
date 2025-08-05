# AI Research Companion 🤖

Your research buddy for interactive document analysis. This web application allows you to upload up to three PDF documents and have an intelligent, suggestion-driven conversation about their combined content.

This tool is designed to accelerate research by helping you quickly query information across multiple sources and discover new avenues of inquiry through AI-generated prompts.

-----

##  Table of Contents

1.  [Key Features](https://www.google.com/search?q=%23-key-features)
2.  [Tech Stack](https://www.google.com/search?q=%23-tech-stack)
3.  [Setup and Installation](https://www.google.com/search?q=%23-setup-and-installation)
4.  [How to Use](https://www.google.com/search?q=%23-how-to-use)
5.  [Contact](https://www.google.com/search?q=%23-contact)

-----

## ✨ Key Features

  * **Dynamic Multi-PDF Upload**: Upload and analyze 1 to 3 PDF documents simultaneously in a single session.
  * **Unified Context**: The AI understands and answers questions based on the combined knowledge from all uploaded documents.
  * **Interactive Q\&A**: Ask direct questions and receive context-aware answers grounded in the provided text.
  * **AI-Powered Suggestions**: Get intelligent topic suggestions after uploading and after each answer to guide your research process.
  * **Session Management**: A clean interface with the ability to clear your session and start over with new documents.
  * **Modern UI**: A polished, easy-on-the-eyes dark theme built with Bootstrap 5.

-----

## 🛠 Tech Stack

  * **Backend**: Python, Flask, LangChain, Google Generative AI (Gemini), FAISS
  * **Frontend**: HTML, CSS, JavaScript, Bootstrap 5

-----

##  Setup and Installation

Follow these steps to get the application running on your local machine.

### Prerequisites

  * Python 3.9 or higher
  * Git
  * A Google AI API Key

### Step-by-Step Guide

1.  **Clone the Repository**

    ```bash
    git clone <your-repository-url>
    cd <repository-folder-name>
    ```

2.  **Create and Activate a Virtual Environment**
    This creates an isolated environment for your project's dependencies.

      * **On Windows:**

        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

      * **On macOS & Linux:**

        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install Dependencies**
    Install all the required Python packages from the `requirements.txt` file.

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables**
    Create a file named **`.env`** in the root of your project folder. This file will securely hold your secret API key. Add your key to it as shown below:

    ```env
    GOOGLE_API_KEY="YOUR_ACTUAL_API_KEY_GOES_HERE"
    ```

    > **Note**: You can get your free API key from the [Google AI Studio](https://aistudio.google.com/app/apikey).

5.  **Run the Application**
    Start the Flask development server.

    ```bash
    python app.py
    ```

    Once the server is running, open your web browser and navigate to the following address:
    ➡ **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

-----

##  How to Use

1.  **Upload Documents**: Click the "Choose File" button to upload your first PDF. You can add up to three PDFs to the same session.
2.  **Start Chatting**: Once a document is processed, you can either type your own question into the input box or click on one of the AI-generated topic suggestions.
3.  **Continue the Conversation**: The AI will provide answers and new follow-up suggestions to keep the discussion going.
4.  **Start Over**: Click the "Clear Session" button at any time to remove all uploaded documents and begin a new research session.

-----

##  Contact

  * **GitHub**: [Srinidhi945](https://www.google.com/search?q=https://github.com/Srinidhi945)
  * **LinkedIn**: www.linkedin.com/in/srinidhi-poreddy
 

-----
