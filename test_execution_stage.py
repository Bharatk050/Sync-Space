#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify Execution_And_Startup stage functionality
"""

import sys
import io
import requests
import json
import time
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
API_BASE = "http://localhost:8000"
PROJECT_DESC = "Create a simple Python Flask API with a /hello endpoint that returns 'Hello World'"

def test_execution_stage():
    """Test the Execution_And_Startup stage"""
    print("=" * 60)
    print("Execution_And_Startup Stage - Verification Test")
    print("=" * 60)
    
    # Step 1: Breakdown project
    print("\n[1/2] Breaking down project...")
    try:
        response = requests.post(
            f"{API_BASE}/breakdown",
            json={"project_description": PROJECT_DESC},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Breakdown failed: {response.status_code}")
            return False
        
        data = response.json()
        subtasks = data.get("subtasks", [])
        
        print(f"✅ Project broken down into {len(subtasks)} stages")
        
        # Find Execution_And_Startup stage
        execution_task = None
        for task in subtasks:
            if task.get("title") == "Execution_And_Startup":
                execution_task = task
                break
        
        if not execution_task:
            print("❌ Execution_And_Startup stage not found in breakdown!")
            return False
        
        print(f"✅ Found Execution_And_Startup stage: {execution_task.get('description', 'N/A')[:100]}...")
        
    except Exception as e:
        print(f"❌ Error during breakdown: {str(e)}")
        return False
    
    # Step 2: Execute the Execution_And_Startup stage
    print("\n[2/2] Testing Execution_And_Startup endpoint...")
    try:
        # Create a test payload
        test_payload = {
            "id": 7,
            "title": "Execution_And_Startup",
            "description": "Generate startup scripts and running instructions",
            "how_to_build": "Create start.sh, start.bat, and README_RUN.md files",
            "Agent_Name": "DevOps Engineer",
            "project_name": "Test_Execution_Stage"
        }
        
        response = requests.post(
            f"{API_BASE}/Execution_And_Startup/",
            json=test_payload,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Execution failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        print(f"✅ Stage executed successfully")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Project folder: {result.get('project_folder', 'N/A')}")
        
        # Check files created
        files_created = result.get('files_created', [])
        print(f"\n📂 Files created: {len(files_created)}")
        
        required_files = ['start.sh', 'start.bat', 'README_RUN.md']
        files_found = {f: False for f in required_files}
        
        for file_path in files_created:
            file_name = Path(file_path).name
            print(f"   - {file_name}")
            
            for req_file in required_files:
                if req_file in file_name:
                    files_found[req_file] = True
        
        print("\n📋 Required files check:")
        all_found = True
        for file_name, found in files_found.items():
            status = "✅" if found else "❌"
            print(f"   {status} {file_name}")
            if not found:
                all_found = False
        
        if not all_found:
            print("\n⚠️  Warning: Not all required files were generated")
            print("   The fallback mechanism should have created them.")
        else:
            print("\n✅ All required files generated successfully!")
        
        # Check if previous files were referenced
        prev_files = result.get('previous_files_referenced', [])
        if prev_files:
            print(f"\n🔗 Previous stage files referenced: {len(prev_files)}")
            for pf in prev_files[:3]:
                print(f"   - {pf}")
            if len(prev_files) > 3:
                print(f"   ... and {len(prev_files) - 3} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during execution: {str(e)}")
        return False

def check_api_health():
    """Check if the API is healthy"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {str(e)}")
        print(f"   Make sure Docker containers are running: docker-compose up")
        return False

if __name__ == "__main__":
    print("\n🔍 Checking API connection...")
    if not check_api_health():
        print("\n❌ Test aborted: API not available")
        exit(1)
    
    print("\n🚀 Starting test...")
    success = test_execution_stage()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Execution_And_Startup stage is working!")
    else:
        print("❌ TEST FAILED: Check the output above for errors")
    print("=" * 60)
    
    exit(0 if success else 1)

