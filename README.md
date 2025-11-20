# FikaTutor Internal Tool

A Python-based internal tool that converts uploaded educational content (PDF, DOC, DOCX, PPT, PPTX) into a structured JSON format.

## Features

- Upload and process multiple file formats (PDF, DOC, DOCX, PPT, PPTX)
- Automatic text extraction from documents
- AI-powered conversion to structured JSON format
- RESTful API with Flask

## Requirements

- **Python 3.8 or higher** (Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, or 3.14)
- pip package manager

## Installation

1. **Clone or navigate to the project directory**

2. **Create a virtual environment (recommended)**
```bash
python -m venv venv
```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Set up environment variables**
   - The `.env` file is already created with the OpenAI API key
   - You can modify it if needed

## Usage

### Start the Server

```bash
python app.py
```

Or with a custom port:
```bash
$env:PORT=8080; python app.py
```

The application will be available at `http://localhost:8000` (or the port you specify)

### Web Interface

Once the server is running, open your browser and navigate to:
- **Web UI**: `http://localhost:8000` - A beautiful, user-friendly interface to upload documents and view JSON results
- **API Endpoint**: `http://localhost:8000/api` - API information endpoint

The web interface supports:
- Drag & drop file upload (single or multiple files)
- Click to browse files (supports selecting multiple files)
- Real-time processing status
- Formatted JSON display
- Copy JSON to clipboard
- Error handling with clear messages
- Multiple file processing with summary

### API Endpoints

#### 1. Health Check
```
GET /health
```

#### 2. Upload and Convert File(s)
```
POST /upload
Content-Type: multipart/form-data

Body: file (PDF, DOC, DOCX, PPT, or PPTX)
- Supports single file or multiple files upload
- For multiple files, use the same key 'file' for each file
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"
```

**Example using Python requests:**
```python
import requests

url = "http://localhost:8000/upload"
files = {"file": open("document.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

**Example using the test script:**
```bash
python test_upload.py path/to/your/document.pdf
```
The test script will upload the file, display the JSON response, and save it to a file (e.g., `document_output.json`).

### Response Format

The API returns a JSON object in the following format:

```json
{
  "subject_name": {
    "title": "Subject Title",
    "description": "Subject description",
    "chapters": [
      {
        "title": "Chapter Title",
        "topics": [
          {
            "topic_id": "topic_1",
            "title": "Topic Title",
            "content": "Detailed content...",
            "examples": ["example 1", "example 2"],
            "real_world_applications": ["application 1"],
            "keywords": ["keyword1", "keyword2"]
          }
        ]
      }
    ]
  }
}
```

## API Documentation

The API follows RESTful conventions. You can test endpoints using:
- **curl** (command line)
- **Postman** or similar API testing tools (see `API_TESTING_GUIDE.md` for detailed instructions)
- **Python requests** library
- **Web UI** at `http://localhost:8000` (browser-based interface)

### Quick Postman Setup:
1. Import the `FikaTutor_API.postman_collection.json` file into Postman
2. Or manually create a POST request to `http://localhost:8000/upload` with form-data (key: `file`, type: File)
3. See `API_TESTING_GUIDE.md` for complete instructions

## Supported File Formats

- **PDF** (.pdf) - Using PyPDF2
- **Word Documents** (.doc, .docx) - Using python-docx
- **PowerPoint Presentations** (.ppt, .pptx) - Using python-pptx

## Framework

This application uses **Flask** as the web framework, providing a lightweight and flexible API server.

## Configuration

### OpenAI Model

You can change the OpenAI model in `json_converter.py`:
- Current: `gpt-4o-mini` (cost-effective)
- Alternative: `gpt-4` or `gpt-4-turbo` (better quality, higher cost)

### API Settings

Modify `app.py` or use environment variables to change:
- Host and port (use `PORT` environment variable)
- CORS settings (configured via flask-cors)
- File size limits: **200MB per request** (default, configurable via `MAX_FILE_SIZE_MB` in `.env`)
- File count limits: **Unlimited by default** (set `MAX_FILES_PER_REQUEST` in `.env` to limit)

**To set a file count limit**, add to your `.env` file:
```
MAX_FILES_PER_REQUEST=10
```
(Set to `0` or don't set it for unlimited files)

**To adjust file size limit**, add to your `.env` file:
```
MAX_FILE_SIZE_MB=500
```
(Default: 200MB. Set to the maximum file size you need, e.g., 500MB, 1000MB, etc.)

**For very large documents**, you can adjust output token limits:
```
MAX_OUTPUT_TOKENS=32000      # 32K tokens for large responses (default: auto-scales 4K-16K based on document size)
```

**Note**: The system automatically handles token limits. Very large documents will be automatically truncated to fit within the model's context window (128,000 tokens for gpt-4o-mini), with a warning message in the output.

## Error Handling

The API handles various error cases:
- Unsupported file types
- File parsing errors
- OpenAI API errors
- Invalid content

## Notes

- **No file count limit** - You can upload as many files as you want (unlimited by default)
- **File size limit**: 200MB per request (all files combined, configurable via `MAX_FILE_SIZE_MB` in `.env`)
- **Automatic token management**: The system automatically truncates content to fit within the model's token limits (128,000 tokens for gpt-4o-mini). Very large documents will be truncated with a warning message.
- **Output token limit**: Auto-scales based on document size (4K-16K tokens, configurable via `MAX_OUTPUT_TOKENS` in `.env`)
- Large files may take longer to process (10-30 seconds per file, longer for very large documents)
- Ensure your OpenAI API key has sufficient credits (each file uses API credits)
- The tool uses temporary files that are automatically cleaned up
- **Processing time**: For multiple files, processing is sequential (one after another), so 10 files may take 2-5 minutes

## Troubleshooting

1. **Import errors**: Make sure all dependencies are installed (`pip install -r requirements.txt`)
2. **OpenAI API errors**: Check your API key in `.env` file and ensure you have credits
3. **File parsing errors**: Ensure the file is not corrupted and is in a supported format
4. **Port already in use**: Change the port in `app.py` or stop the process using port 8000
5. **413 Request Entity Too Large**: Increase the `MAX_FILE_SIZE_MB` value in your `.env` file (default: 200MB)
6. **Token limit errors**: The system now automatically handles token limits. If you still encounter issues with very large documents, the content will be automatically truncated. Consider processing very large documents in smaller chunks if you need complete content coverage.

