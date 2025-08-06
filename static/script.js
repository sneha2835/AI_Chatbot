// static/script.js - Corrected and Final Version

document.addEventListener('DOMContentLoaded', () => {
    // --- Get all necessary DOM elements ---
    const pdfUpload = document.getElementById('pdf-upload');
    const statusDiv = document.getElementById('status');
    const chatForm = document.getElementById('chat-form');
    const questionInput = document.getElementById('question-input');
    const sendBtn = document.getElementById('send-btn');
    const chatWindow = document.getElementById('chat-window');
    const suggestionsBox = document.getElementById('suggestions-box');
    const suggestionsList = document.getElementById('suggestions-list');
    
    // NEW: Elements for multi-file display and clearing the session
    const uploadedFilesBox = document.getElementById('uploaded-files-box');
    const uploadedFilesList = document.getElementById('uploaded-files-list');
    const clearSessionBtn = document.getElementById('clear-session-btn');

    // --- Event Listener for PDF Upload ---
    pdfUpload.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        statusDiv.textContent = 'Uploading and processing... This may take a moment.';
        pdfUpload.disabled = true; // Disable while one is processing

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', { method: 'POST', body: formData });
            const result = await response.json();

            if (result.success) {
                statusDiv.textContent = result.message;
                updateUploadedFilesList(result.uploaded_files);
                updateSuggestions(result.suggestions);

                // Check if the max file limit has been reached
                if (result.uploaded_files.length >= 3) {
                    pdfUpload.disabled = true;
                    statusDiv.textContent = "Maximum of 3 PDFs uploaded. Clear session to start over.";
                } else {
                    pdfUpload.disabled = false; // Re-enable if limit not reached
                }
                
                // Enable chat now that a document is ready
                questionInput.disabled = false;
                sendBtn.disabled = false;

            } else {
                // Handle errors from the backend, like the max limit error
                statusDiv.textContent = `Error: ${result.error}`;
                pdfUpload.disabled = false; // Re-enable on failure
            }
        } catch (error) {
            statusDiv.textContent = 'An unexpected error occurred during upload.';
            pdfUpload.disabled = false; // Re-enable on failure
        }
    });

    // --- Event Listener for Clearing the Session ---
    clearSessionBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/clear', { method: 'POST' });
            const result = await response.json();

            if (result.success) {
                // Reset the entire UI to its initial state
                chatWindow.innerHTML = '';
                updateUploadedFilesList([]);
                updateSuggestions([]);
                statusDiv.textContent = 'Please upload a PDF to begin.';
                questionInput.value = '';
                questionInput.disabled = true;
                sendBtn.disabled = true;
                pdfUpload.disabled = false;
                pdfUpload.value = ''; // Clear the file input
            }
        } catch (error) {
            statusDiv.textContent = "Error clearing session.";
        }
    });

    // --- Event Listener for Sending a Message ---
    chatForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const question = questionInput.value.trim();
        const exitCommands = ['bye', 'exit', 'thank you'];
        if (exitCommands.includes(question.toLowerCase())) {
            appendMessage("Goodbye! Session ended.", 'bot-msg');
            questionInput.disabled = true;
            sendBtn.disabled = true;
            suggestionsBox.style.display = 'none';
            return;
        }
        if (question) {
            submitQuestion(question);
        }
    });

    // --- Event Listener for Clicking a Suggestion ---
    suggestionsList.addEventListener('click', (event) => {
        if (event.target && event.target.nodeName === "LI") {
            submitQuestion(event.target.textContent);
        }
    });
    
    // --- Central Function to Handle Asking a Question ---
    async function submitQuestion(question) {
        appendMessage(question, 'user-msg');
        questionInput.value = '';
        questionInput.disabled = true;
        sendBtn.disabled = true;
        suggestionsBox.style.display = 'none';

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });
            const result = await response.json();

            if (result.answer) {
                appendMessage(result.answer, 'bot-msg');
                updateSuggestions(result.suggestions);
            } else {
                appendMessage(`Error: ${result.error || 'Could not get an answer.'}`, 'bot-msg');
            }
        } catch (error) {
            appendMessage('An error occurred. Please try again.', 'bot-msg');
        } finally {
            questionInput.disabled = false;
            sendBtn.disabled = false;
            questionInput.focus();
        }
    }
    
    // --- NEW: Function to display the list of uploaded files ---
    function updateUploadedFilesList(filenames) {
        uploadedFilesList.innerHTML = '';
        if (filenames && filenames.length > 0) {
            filenames.forEach(name => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = name;
                uploadedFilesList.appendChild(li);
            });
            uploadedFilesBox.style.display = 'block';
        } else {
            uploadedFilesBox.style.display = 'none';
        }
    }

    // --- Function to Update the Suggestions UI ---
    function updateSuggestions(suggestions) {
        suggestionsList.innerHTML = '';
        if (suggestions && suggestions.length > 0) {
            suggestions.forEach(q => {
                const li = document.createElement('li');
                li.className = 'list-group-item list-group-item-action';
                li.style.cursor = 'pointer';
                li.textContent = q;
                suggestionsList.appendChild(li);
            });
            suggestionsBox.style.display = 'block';
        } else {
            suggestionsBox.style.display = 'none';
        }
    }

    // --- Function to Add a Message to the Chat Window ---
    function appendMessage(text, className) {
        const msgWrapper = document.createElement('div');
        const msgDiv = document.createElement('div');
        msgWrapper.appendChild(msgDiv);
        msgDiv.classList.add("msg", className);
        msgDiv.textContent = text;
        chatWindow.appendChild(msgWrapper);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});