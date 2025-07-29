import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print('=== Testing VLM.run Document Processing ===')

try:
    from vlmrun.client import VLMRun
    
    # Set up API key
    vlm_api_key = os.getenv('VLMRUN_API_KEY') or os.getenv('VLM_API_KEY')
    print(f'Using API key: {vlm_api_key[:10]}...{vlm_api_key[-5:]}')
    
    os.environ['VLMRUN_API_KEY'] = vlm_api_key
    client = VLMRun()
    
    print('✅ VLMRun client initialized')
    
    # Create a simple test PDF content (minimal PDF structure)
    test_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000125 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'
    
    # Test with a temporary PDF file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(test_pdf_content)
        temp_file_path = temp_file.name
    
    try:
        print(f'Testing with temp file: {temp_file_path}')
        response = client.document.generate(
            file=Path(temp_file_path),
            domain='document.resume'
        )
        
        print('✅ API call successful!')
        print(f'Response type: {type(response)}')
        print(f'Response status: {getattr(response, "status", "unknown")}')
        print(f'Response attributes: {[attr for attr in dir(response) if not attr.startswith("_")]}')
        
        if hasattr(response, 'response'):
            print(f'Response data preview: {str(response.response)[:200]}...')
        
    except Exception as api_error:
        print(f'❌ API call failed: {api_error}')
        print(f'Error type: {type(api_error)}')
        
        # Check if it's a specific HTTP error
        if hasattr(api_error, 'response'):
            print(f'HTTP Status Code: {api_error.response.status_code}')
            print(f'HTTP Response Text: {api_error.response.text}')
        
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            
except Exception as e:
    print(f'❌ Setup error: {e}')
    import traceback
    traceback.print_exc()

print('\n=== Alternative Test: Check API Key Validity ===')
try:
    import requests
    
    vlm_api_key = os.getenv('VLMRUN_API_KEY') or os.getenv('VLM_API_KEY')
    
    # Test API key with a simple request to VLM.run
    headers = {
        'Authorization': f'Bearer {vlm_api_key}',
        'Content-Type': 'application/json'
    }
    
    # Try a simple API endpoint (this is a guess at the API structure)
    test_url = 'https://api.vlm.run/v1/health'  # or similar endpoint
    
    print(f'Testing API key with direct HTTP request...')
    response = requests.get(test_url, headers=headers, timeout=10)
    
    print(f'HTTP Status: {response.status_code}')
    print(f'Response: {response.text[:200]}...')
    
except Exception as http_error:
    print(f'HTTP test failed: {http_error}')
