#!/usr/bin/env python
"""
Test script để kiểm tra các endpoints
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test server health"""
    print("🔍 Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Server is running (status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_list_documents():
    """Test list documents endpoint"""
    print("\n🔍 Testing GET /api/documents/...")
    try:
        response = requests.get(f"{BASE_URL}/api/documents/")
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"✅ Documents count: {len(data.get('documents', []))}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_upload_file(file_path=None):
    """Test upload file endpoint"""
    print("\n🔍 Testing POST /api/documents/upload/...")
    
    if not file_path:
        # Create a test file
        file_path = "/tmp/test_document.txt"
        with open(file_path, 'w') as f:
            f.write("This is a test document for RAG system.\n" * 50)
        print(f"📄 Created test file: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/api/documents/upload/", files=files)
        
        print(f"✅ Status: {response.status_code}")
        
        # Check if response is JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"❌ Response is not JSON: {response.text[:200]}")
            return None
        
        if response.status_code == 201:
            doc = data.get('document', {})
            print(f"✅ Document uploaded: ID={doc.get('id')}, Name={doc.get('name')}, Status={doc.get('status')}")
            return doc.get('id')
        else:
            print(f"⚠️ Response: {json.dumps(data, indent=2)}")
            if 'document_id' in data:
                return data['document_id']
            return None
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_document_status(doc_id):
    """Test document detail endpoint"""
    print(f"\n🔍 Testing GET /api/documents/{doc_id}/...")
    try:
        response = requests.get(f"{BASE_URL}/api/documents/{doc_id}/")
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"✅ Document: {data.get('name')}, Status: {data.get('status')}, Chunks: {data.get('num_chunks', 0)}")
        return data
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def wait_for_processing(doc_id, max_wait=60):
    """Wait for document processing to complete"""
    print(f"\n⏳ Waiting for document {doc_id} to be processed (max {max_wait}s)...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        doc = test_document_status(doc_id)
        if doc:
            status = doc.get('status')
            if status == 'completed':
                print(f"✅ Document processing completed! Chunks: {doc.get('num_chunks', 0)}")
                return True
            elif status == 'failed':
                print(f"❌ Document processing failed: {doc.get('error_message', 'Unknown error')}")
                return False
            else:
                print(f"⏳ Status: {status}...")
        
        time.sleep(2)
    
    print(f"⏰ Timeout after {max_wait}s")
    return False

def test_chat(doc_id):
    """Test chat endpoint"""
    print(f"\n🔍 Testing POST /api/chat/stream/ with document {doc_id}...")
    try:
        payload = {
            "document_id": doc_id,
            "messages": [
                {"role": "user", "content": "What is this document about?"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream/",
            json=payload,
            stream=True,
            timeout=30
        )
        
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📝 Chat response (streaming):")
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            if 'content' in data:
                                content = data['content']
                                full_response += content
                                print(content, end='', flush=True)
                            elif 'error' in data:
                                print(f"\n❌ Error: {data['error']}")
                                return False
                        except json.JSONDecodeError:
                            continue
            
            print(f"\n✅ Chat completed! Response length: {len(full_response)} chars")
            return True
        else:
            print(f"❌ Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing VeritasAI Django RAG System")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        sys.exit(1)
    
    # Test 2: List documents
    test_list_documents()
    
    # Test 3: Upload file
    doc_id = test_upload_file()
    if not doc_id:
        print("\n❌ Upload failed, stopping tests")
        sys.exit(1)
    
    # Test 4: Wait for processing
    if wait_for_processing(doc_id):
        # Test 5: Chat
        test_chat(doc_id)
    else:
        print("\n⚠️ Document processing not completed, skipping chat test")
    
    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()

