import os
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import tempfile
import logging

from file_parser import FileParser
from json_converter import JSONConverter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure file upload limits
# Maximum file size per file (default: 200MB, can be overridden via MAX_FILE_SIZE_MB env var)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "200"))  # Default: 200MB
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes

# Maximum number of files per request (set to None for unlimited, or specify a number)
MAX_FILES_PER_REQUEST = int(os.getenv("MAX_FILES_PER_REQUEST", "0"))  # 0 = unlimited

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=openai_api_key)

# Initialize services
file_parser = FileParser()
json_converter = JSONConverter(client)


@app.route("/", methods=["GET"])
def root():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Upload one or more files (PDF, DOC, DOCX, PPT, PPTX) and convert them to JSON format.
    Supports single file or multiple files upload.
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        # Get all files (supports single or multiple file uploads)
        files = request.files.getlist('file')
        
        # Filter out empty files
        files = [f for f in files if f.filename != '']
        
        if not files:
            return jsonify({"error": "No file selected"}), 400
        
        # Check file count limit if configured
        if MAX_FILES_PER_REQUEST > 0 and len(files) > MAX_FILES_PER_REQUEST:
            return jsonify({
                "error": f"Too many files. Maximum {MAX_FILES_PER_REQUEST} files allowed per request."
            }), 400
        
        # Validate file types
        allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx']
        results = []
        temp_files = []
        
        try:
            for file in files:
                file_extension = os.path.splitext(file.filename)[1].lower()
                
                if file_extension not in allowed_extensions:
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "error": f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
                    })
                    continue
                
                logger.info(f"Processing file: {file.filename}")
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = temp_file.name
                    temp_files.append(temp_file_path)
                
                try:
                    # Parse file content
                    logger.info(f"Extracting text from {file.filename}...")
                    extracted_text = file_parser.parse_file(temp_file_path, file_extension)
                    
                    if not extracted_text or len(extracted_text.strip()) < 50:
                        results.append({
                            "filename": file.filename,
                            "status": "error",
                            "error": "Could not extract sufficient text from the file. Please ensure the file contains readable content."
                        })
                        continue
                    
                    logger.info(f"Extracted {len(extracted_text)} characters from {file.filename}")
                    
                    # Convert to JSON format using OpenAI
                    logger.info(f"Converting {file.filename} to JSON format...")
                    json_output = json_converter.convert_to_json(extracted_text, file.filename)
                    
                    logger.info(f"Conversion completed successfully for {file.filename}")
                    
                    results.append({
                        "filename": file.filename,
                        "status": "success",
                        "data": json_output
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing {file.filename}: {str(e)}", exc_info=True)
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "error": f"Error processing file: {str(e)}"
                    })
            
            # Prepare response
            successful = sum(1 for r in results if r["status"] == "success")
            failed = len(results) - successful
            
            response = {
                "results": results,
                "summary": {
                    "total_files": len(files),
                    "successful": successful,
                    "failed": failed
                }
            }
            
            # If only one file was uploaded, return the data directly (backward compatibility)
            if len(files) == 1:
                if results[0]["status"] == "success":
                    return jsonify(results[0]["data"])
                else:
                    return jsonify({"error": results[0]["error"]}), 400
            
            # For multiple files, return the structured response
            return jsonify(response)
            
        finally:
            # Clean up all temporary files
            for temp_file_path in temp_files:
                if os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except Exception as e:
                        logger.warning(f"Could not delete temp file {temp_file_path}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error processing files: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing files: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})


@app.route("/api", methods=["GET"])
def api_info():
    return jsonify({"message": "FikaTutor Internal Tool API", "status": "running"})


if __name__ == "__main__":
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
