#!/usr/bin/env python3
"""
Test VLM.run API with alternative approaches that might not require file upload permissions
"""

import os
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from vlmrun.client import VLMRun
    print("✅ VLM.run SDK imported successfully!")
except ImportError as e:
    print(f"❌ VLM.run SDK not available: {e}")
    sys.exit(1)

def test_vlm_alternatives():
    """Test different VLM.run approaches"""
    
    vlm_api_key = os.getenv("VLMRUN_API_KEY") or os.getenv("VLM_API_KEY")
    if not vlm_api_key:
        print("❌ No VLM API key found")
        return
    
    print(f"=== Testing VLM.run Alternative Approaches ===")
    print(f"Using API key: {vlm_api_key[:12]}...{vlm_api_key[-5:]}")
    
    try:
        # Initialize client
        os.environ["VLMRUN_API_KEY"] = vlm_api_key
        client = VLMRun()
        print("✅ VLMRun client initialized")
        
        # Test 1: Try with explicit purpose parameter
        print("\n=== Test 1: Document processing with explicit purpose ===")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(b"Sample PDF content for testing")
            temp_file_path = temp_file.name
        
        try:
            # Try with different configuration
            response = client.document.generate(
                file=Path(temp_file_path),
                domain="document.resume",
                # Maybe try without automatic file upload?
            )
            print(f"✅ Test 1 success: {response}")
        except Exception as e:
            print(f"❌ Test 1 failed: {e}")
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        # Test 2: Check if we can manually upload files first
        print("\n=== Test 2: Manual file upload ===")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(b"Sample PDF content for testing")
                temp_file_path = temp_file.name
            
            # Try explicit file upload
            file_response = client.files.upload(
                file=temp_file_path,
                purpose="assistants"  # Try explicit purpose
            )
            print(f"✅ File upload success: {file_response}")
            
            # Now try to process the uploaded file
            response = client.document.generate(
                url=file_response.url,  # Use URL instead of file
                domain="document.resume"
            )
            print(f"✅ URL processing success: {response}")
            
        except Exception as e:
            print(f"❌ Test 2 failed: {e}")
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        # Test 3: Check available domains
        print("\n=== Test 3: Check available domains ===")
        try:
            domains = client.hub.list_domains()
            print(f"✅ Available domains: {[d.name for d in domains if 'resume' in d.name.lower()]}")
        except Exception as e:
            print(f"❌ Test 3 failed: {e}")
        
        # Test 4: Check file upload purposes
        print("\n=== Test 4: Try different file purposes ===")
        purposes_to_try = ["vision", "batch", "datasets"]
        
        for purpose in purposes_to_try:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(b"Sample PDF content for testing")
                    temp_file_path = temp_file.name
                
                file_response = client.files.upload(
                    file=temp_file_path,
                    purpose=purpose
                )
                print(f"✅ Upload with purpose '{purpose}' success: {file_response.id}")
                
                # Try to delete the test file
                client.files.delete(file_response.id)
                print(f"✅ Deleted test file: {file_response.id}")
                
            except Exception as e:
                print(f"❌ Upload with purpose '{purpose}' failed: {e}")
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"❌ General error: {e}")

if __name__ == "__main__":
    test_vlm_alternatives()
