import streamlit as st
import requests
from groq import Groq
import os
from datetime import datetime
import re
import json
from pathlib import Path
from dotenv import load_dotenv
import subprocess

def fetch_docker_files(container_name: str, source_path: str, dest_path: str) -> bool:
    """Fetch files from Docker container to local path"""
    try:
        # Create destination directory with proper permissions
        dest_path = Path(dest_path)
        dest_path.mkdir(parents=True, exist_ok=True, mode=0o777)
        
        # Copy files from container to host
        cmd = f'docker cp {container_name}:{source_path} "{dest_path}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Fix permissions on copied files
            subprocess.run(f'icacls "{dest_path}" /grant Everyone:F /T', shell=True)
            st.success("✅ Files fetched successfully from Docker container")
            return True
        else:
            st.error(f"Failed to fetch files: {result.stderr}")
            return False
            
    except Exception as e:
        st.error(f"Error fetching files from Docker: {str(e)}")
        return False

# Add Groq client setup
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY environment variable is not set!")
    client = None
else:
    client = Groq(api_key=GROQ_API_KEY)

def sanitize_project_name(name):
    """Sanitize the project name to be file system friendly"""
    # Remove newlines and leading/trailing whitespace
    name = name.strip().replace('\n', ' ').replace('\r', '')
    
    # Replace invalid characters and spaces with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)  # Windows invalid chars
    sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with single underscore
    
    # Remove any non-ASCII characters
    sanitized = ''.join(char for char in sanitized if ord(char) < 128)
    
    # Remove duplicate underscores and strip leading/trailing underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    
    # Ensure the name isn't empty after sanitization
    if not sanitized:
        return f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    return sanitized

def generate_unique_project_name(project_description):
    """Generate a unique project name with better error handling and file saving"""
    if not client:
        return f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    prompt = f"""Given this project description: '{project_description}'
    Generate a unique, memorable, and professional project name that is:
    - Maximum 3 words
    - No special characters or symbols
    - Only use letters, numbers, and single spaces
    - Easy to remember
    - Related to the project's purpose
    Return only the name, nothing else."""
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=50
        )
        
        generated_name = chat_completion.choices[0].message.content.strip()
        sanitized_name = sanitize_project_name(generated_name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_name = f"{sanitized_name}_{timestamp}"
        
        # Ensure the name isn't too long for file systems
        if len(unique_name) > 240:
            unique_name = f"{unique_name[:230]}_{timestamp}"
        
        # Create project directory
        project_dir = Path(unique_name)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Save project info
        project_info = {
            "name": unique_name,
            "original_description": project_description,
            "generated_name": generated_name,
            "created_at": datetime.now().isoformat(),
            "sanitized_name": sanitized_name
        }
        
        # Save project info to JSON file
        info_file = project_dir / "project_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(project_info, f, indent=2)
            
        # Save project description
        desc_file = project_dir / "description.md"
        with open(desc_file, 'w', encoding='utf-8') as f:
            f.write(f"# {unique_name}\n\n## Project Description\n\n{project_description}")
        
        return unique_name
    except Exception as e:
        st.warning(f"Failed to generate name using Groq: {str(e)}")
        fallback_name = f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        Path(fallback_name).mkdir(parents=True, exist_ok=True)
        return fallback_name

# FastAPI endpoints
API_BREAKDOWN = "http://backend:8000/breakdown"
API_ENDPOINTS = {
    "Requirements_GatheringAnd_Analysis": "http://backend:8000/Requirements_GatheringAnd_Analysis/",
    "Design": "http://backend:8000/Design/",
    "Implementation_Development": "http://backend:8000/Implementation_Development/",
    "Testing_Quality_Assurance": "http://backend:8000/Testing_Quality_Assurance/",
    "Deployment": "http://backend:8000/Deployment/",
    "Maintenance": "http://backend:8000/Maintenance/"
}

st.set_page_config(page_title="Project Breakdown", page_icon="🛠️", layout="wide")
st.title("🛠️ Project Breakdown & Agent Assignment")

# --------------------------
# Session state setup
# --------------------------
if "subtasks" not in st.session_state:
    st.session_state.subtasks = []
if "exec_results" not in st.session_state:
    st.session_state.exec_results = {}
if "project_name" not in st.session_state:
    st.session_state.project_name = ""

# --------------------------
# User Input
# --------------------------
project_desc = st.text_area("Enter your project description:", height=150)

def validate_project_description(description):
    """Validate the project description"""
    if not description:
        return False, "Project description cannot be empty."
    if len(description) < 10:
        return False, "Project description is too short. Please provide more details."
    if len(description) > 5000:
        return False, "Project description is too long. Please be more concise."
    return True, ""

if st.button("🔍 Breakdown Project"):
    is_valid, error_message = validate_project_description(project_desc)
    
    if not is_valid:
        st.warning(error_message)
    else:
        with st.spinner("Breaking down project..."):
            try:
                # Generate unique project name first
                unique_project_name = generate_unique_project_name(project_desc)
                
                response = requests.post(
                    API_BREAKDOWN, 
                    json={"project_description": project_desc},  # Simplified payload
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.subtasks = data.get("subtasks", [])
                    st.session_state.project_name = unique_project_name
                    st.success("✅ Project breakdown completed!")
                    st.info(f"📎 Project Name: {unique_project_name}")
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")
            except requests.Timeout:
                st.error("Request timed out. Please try again.")
            except requests.ConnectionError:
                st.error("Failed to connect to the API. Please check if the server is running.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

# --------------------------
# File Display Function
# --------------------------
def display_generated_files(exec_data):
    """Display generated files with comprehensive file type handling"""
    if not exec_data:
        return
    
    st.markdown("### 📂 Generated Files")
    
    # Handle Docker container paths
    docker_project_folder = Path("/sync_space/output") / exec_data.get('project_folder', '').split('/')[-1]
    local_project_folder = Path(exec_data.get('project_folder', ''))
    
    # Try Docker path first, then local path
    if docker_project_folder.exists():
        project_folder = docker_project_folder
    elif local_project_folder.exists():
        project_folder = local_project_folder
    else:
        st.error("Project folder not found in either Docker container or local path")
        return

    # File type configurations
    FILE_TYPES = {
        # Documentation
        '.md': {'icon': '📝', 'display': 'markdown', 'mime': 'text/markdown'},
        '.txt': {'icon': '📄', 'display': 'text', 'mime': 'text/plain'},
        
        # Code
        '.py': {'icon': '🐍', 'display': 'code', 'mime': 'text/x-python'},
        '.js': {'icon': '🟨', 'display': 'code', 'mime': 'text/javascript'},
        '.ts': {'icon': '📘', 'display': 'code', 'mime': 'text/typescript'},
        '.java': {'icon': '☕', 'display': 'code', 'mime': 'text/x-java'},
        '.html': {'icon': '🌐', 'display': 'code', 'mime': 'text/html'},
        '.css': {'icon': '🎨', 'display': 'code', 'mime': 'text/css'},
        
        # Tests
        '_test.py': {'icon': '🧪', 'display': 'code', 'mime': 'text/x-python'},
        '.spec.js': {'icon': '🧪', 'display': 'code', 'mime': 'text/javascript'},
        
        # Configuration
        '.yaml': {'icon': '⚙️', 'display': 'code', 'mime': 'text/yaml'},
        '.yml': {'icon': '⚙️', 'display': 'code', 'mime': 'text/yaml'},
        '.json': {'icon': '📊', 'display': 'json', 'mime': 'application/json'},
        '.env': {'icon': '🔐', 'display': 'code', 'mime': 'text/plain'},
        '.conf': {'icon': '⚙️', 'display': 'code', 'mime': 'text/plain'},
        
        # Deployment
        'Dockerfile': {'icon': '🐳', 'display': 'code', 'mime': 'text/plain'},
        'docker-compose.yml': {'icon': '🐋', 'display': 'code', 'mime': 'text/yaml'},
        
        # Database
        '.sql': {'icon': '🗄️', 'display': 'code', 'mime': 'text/x-sql'},
        
        # Diagrams
        '.puml': {'icon': '📊', 'display': 'code', 'mime': 'text/plain'},
        
        # Scripts
        '.sh': {'icon': '⚡', 'display': 'code', 'mime': 'text/x-sh'},
        '.bat': {'icon': '⚡', 'display': 'code', 'mime': 'text/plain'},
        
        # Monitoring
        '.log': {'icon': '📝', 'display': 'text', 'mime': 'text/plain'},
    }
    
    # Group files by type
    files_by_type = {}
    for file_path in exec_data.get('files_created', []):
        file = Path(file_path)
        if not file.exists():
            continue
            
        file_type = file.suffix.lower()
        if '_test' in file.name:
            type_key = 'Tests'
        elif file.name == 'Dockerfile':
            type_key = 'Deployment'
        elif file_type in ['.yml', '.yaml', '.json', '.env', '.conf']:
            type_key = 'Configuration'
        elif file_type in ['.py', '.js', '.ts', '.java']:
            type_key = 'Source Code'
        elif file_type in ['.md', '.txt']:
            type_key = 'Documentation'
        else:
            type_key = 'Other'
            
        if type_key not in files_by_type:
            files_by_type[type_key] = []
        files_by_type[type_key].append(file)

    # Display files by group
    for group, files in files_by_type.items():
        st.markdown(f"#### {group}")
        for file in sorted(files):
            file_type = FILE_TYPES.get(file.suffix.lower(), 
                                    {'icon': '📄', 'display': 'text', 'mime': 'text/plain'})
            
            with st.expander(f"{file_type['icon']} {file.name}"):
                try:
                    if file_type['display'] == 'markdown':
                        content = file.read_text(encoding='utf-8')
                        st.markdown(content)
                    
                    elif file_type['display'] == 'code':
                        content = file.read_text(encoding='utf-8')
                        st.code(content, language=file.suffix.lstrip('.'))
                    
                    elif file_type['display'] == 'json':
                        content = file.read_text(encoding='utf-8')
                        st.json(json.loads(content))
                    
                    else:  # Default text display
                        content = file.read_text(encoding='utf-8')
                        st.text(content)
                    
                    # File metadata
                    file_stat = file.stat()
                    st.caption(f"""
                    Last modified: {datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}
                    Size: {file_stat.st_size/1024:.2f} KB
                    """)
                    
                    # Download button
                    with open(file, 'rb') as f:
                        st.download_button(
                            label=f"⬇️ Download {file.name}",
                            data=f.read(),
                            file_name=file.name,
                            mime=file_type['mime']
                        )
                    
                except Exception as e:
                    st.error(f"Error displaying file {file.name}: {str(e)}")

# --------------------------
# Show Subtasks
# --------------------------
if st.session_state.subtasks:
    st.subheader("📝 Subtasks")
    for s in st.session_state.subtasks:
        with st.expander(f"📌 {s['title']}"):
            st.write(f"**Description:** {s['description']}")
            st.write(f"**How to Build:** {s['how_to_build']}")
            st.write(f"**Agent Name:** {s['Agent_Name']}")
            if 'required_files' in s:
                st.write("**Required Files:**", ', '.join(s['required_files']))
            if 'dependencies' in s:
                st.write("**Dependencies:**", ', '.join(s['dependencies']))
            if 'acceptance_criteria' in s:
                st.write("**Acceptance Criteria:**")
                for criterion in s['acceptance_criteria']:
                    st.write(f"- {criterion}")

            # Execute subtask
            endpoint_url = API_ENDPOINTS.get(s["title"], None)
            
            if endpoint_url:
                if st.button(f"⚡ Build Subtask: {s['title']}", key=f"build_{s['id']}"):
                    with st.spinner(f"Building {s['title']}..."):
                        # Safer ID handling
                        try:
                            task_id = int(str(s["id"]).replace("task_", ""))
                        except (ValueError, TypeError):
                            task_id = 0  # fallback ID
                            
                        # Ensure how_to_build is a string
                        if isinstance(s["how_to_build"], (dict, list)):
                            how_to_build = json.dumps(s["how_to_build"])
                        else:
                            how_to_build = str(s["how_to_build"])
                        
                        payload = {
                            "id": task_id,
                            "title": s["title"],
                            "description": s["description"],
                            "how_to_build": how_to_build,
                            "Agent_Name": s["Agent_Name"],
                            "project_name": st.session_state.project_name
                        }
                        
                        try:
                            exec_response = requests.post(endpoint_url, json=payload)
                            if exec_response.status_code == 200:
                                exec_data = exec_response.json()
                                st.session_state.exec_results[s['id']] = exec_data
                                
                                # Fetch files from Docker container
                                docker_path = f"/sync_space/output/{st.session_state.project_name}"
                                local_path = f"./output/{st.session_state.project_name}"
                                
                                if fetch_docker_files("fastapi-backend", docker_path, local_path):
                                    # Update exec_data with local path
                                    exec_data['project_folder'] = local_path
                                    st.success(f"✅ Subtask completed successfully!")
                                    display_generated_files(exec_data)
                                else:
                                    st.warning("⚠️ Subtask completed but files could not be fetched")
                            else:
                                st.error(f"Build failed: {exec_response.text}")
                        except Exception as e:
                            st.error(f"Failed to execute subtask: {e}")
            else:
                st.warning("No API endpoint configured for this subtask.")

