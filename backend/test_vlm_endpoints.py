#!/usr/bin/env python3
"""
Check all VLM.run endpoints that are being used
"""

import os
import sys
import tempfile
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def analyze_vlm_endpoints():
    """Analyze all VLM.run endpoints we've encountered"""
    
    print("=== VLM.run Endpoints Analysis ===")
    
    # List all endpoints we've seen in logs and code
    endpoints_found = [
        "https://api.vlm.run/v1/health",
        "https://api.vlm.run/v1/files?purpose=assistants", 
        "https://api.vlm.run/v1/files",
        "https://vlm.run/dashboard",
    ]
    
    print("📋 Endpoints discovered so far:")
    for i, endpoint in enumerate(endpoints_found, 1):
        print(f"{i}. {endpoint}")
    
    # Test basic connectivity to known working endpoint
    vlm_api_key = os.getenv("VLMRUN_API_KEY") or os.getenv("VLM_API_KEY")
    if not vlm_api_key:
        print("❌ No VLM API key found")
        return
    
    print(f"\n🔑 Using API key: {vlm_api_key[:12]}...{vlm_api_key[-5:]}")
    
    headers = {
        'Authorization': f'Bearer {vlm_api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test different endpoints
    test_endpoints = [
        "https://api.vlm.run/v1/health",
        "https://api.vlm.run/v1/",
        "https://api.vlm.run/",
        "https://api.vlm.run/v1/status",
        "https://api.vlm.run/v1/models",
        "https://api.vlm.run/v1/domains",
        "https://api.vlm.run/v1/predictions",
    ]
    
    print("\n🔍 Testing different endpoints:")
    for endpoint in test_endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"✅ {endpoint} → {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
                except:
                    print(f"   Response: {response.text[:100]}...")
        except Exception as e:
            print(f"❌ {endpoint} → Error: {e}")
    
    # Test file endpoints specifically
    print("\n📁 Testing file-related endpoints:")
    file_endpoints = [
        "https://api.vlm.run/v1/files",
        "https://api.vlm.run/v1/files?limit=1",
    ]
    
    for endpoint in file_endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"📁 {endpoint} → {response.status_code}")
            if response.status_code != 200:
                print(f"   Error: {response.text[:200]}")
            else:
                try:
                    data = response.json()
                    print(f"   Success: {data}")
                except:
                    print(f"   Response: {response.text[:100]}")
        except Exception as e:
            print(f"❌ {endpoint} → Error: {e}")

if __name__ == "__main__":
    analyze_vlm_endpoints()
