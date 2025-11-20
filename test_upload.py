"""
Simple test script to test the file upload API.
Usage: python test_upload.py <path_to_file>
"""
import sys
import requests
import json

def test_upload(file_path: str):
    """Test the upload endpoint with a file."""
    url = "http://localhost:8000/upload"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.split('/')[-1], f, 'application/octet-stream')}
            print(f"Uploading {file_path}...")
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            print("\n✅ Success! JSON output:")
            print(json.dumps(response.json(), indent=2))
            
            # Optionally save to file
            output_file = file_path.rsplit('.', 1)[0] + '_output.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, indent=2, ensure_ascii=False)
            print(f"\n💾 Output saved to: {output_file}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
    
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_upload.py <path_to_file>")
        sys.exit(1)
    
    test_upload(sys.argv[1])

