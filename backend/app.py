from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from resume_tailor import tailor_resume_to_job, upload_resume_to_db, retrieve_relevant_context
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
CORS(app)

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    """
    Upload a resume/details file and store it in the vector database.
    
    Returns:
    {
        "success": true,
        "chunks_stored": number,
        "message": "string"
    }
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed. Use TXT, PDF, or DOCX"}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process and store in vector database
        chunks_stored = upload_resume_to_db(filepath)
        
        # Clean up temporary file
        os.remove(filepath)
        
        return jsonify({
            "success": True,
            "chunks_stored": chunks_stored,
            "message": f"Successfully uploaded and stored {chunks_stored} sections"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tailor-resume', methods=['POST'])
def tailor_resume_endpoint():
    """
    Tailor resume based on job description, using vector database context.
    
    Expected JSON:
    {
        "job_description": "string - job description"
    }
    
    Returns:
    {
        "tailored_resume": "string - tailored resume",
        "suggestions": ["string - list of suggestions"],
        "match_score": "number - 0-100 match percentage",
        "retrieved_context": ["string - relevant sections from database"]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        job_description = data.get('job_description', '').strip()
        
        if not job_description:
            return jsonify({"error": "Job description is required"}), 400
        
        # Retrieve relevant context from vector database
        retrieved_context = retrieve_relevant_context(job_description)
        
        # Tailor resume using retrieved context and job description
        result = tailor_resume_to_job(retrieved_context, job_description)
        
        # Add retrieved context to result
        result['retrieved_context'] = retrieved_context
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

