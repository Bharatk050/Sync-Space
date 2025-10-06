import os
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq  # official Groq client
from dotenv import load_dotenv
import json
import re
from pathlib import Path
from datetime import datetime
from time import sleep
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception

# -----------------------------
# Load API key
# -----------------------------
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=groq_api_key)
app = FastAPI()

# -----------------------------
# Global Configuration
# -----------------------------
DEFAULT_MODEL = "llama-3.3-70b-versatile"  # Primary model
BACKUP_MODEL = "deepseek-r1-distill-llama-70b"             # Fallback model

# -----------------------------
# Request body formats
# -----------------------------
class ProjectRequest(BaseModel):
    project_description: str

class SubtaskRequest(BaseModel):
    id: int
    title: str
    description: str
    how_to_build: str
    Agent_Name: str
    project_name: str  # folder name for saving

# -----------------------------
# JSON Parser
# -----------------------------
def parse_llm_json(response_text):
    """Extract JSON from LLM response safely. Returns a list of dicts."""
    try:
        match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
        if match:
            json_text = match.group(0)
            subtasks = json.loads(json_text)
        else:
            subtasks = [{
                "id": 0,
                "title": "Parsing Error",
                "description": response_text,
                "how_to_build": "",
                "Agent_Name": "System"
            }]
    except Exception as e:
        subtasks = [{
            "id": 0,
            "title": "Parsing Error",
            "description": str(e),
            "how_to_build": response_text,
            "Agent_Name": "System"
        }]
    return subtasks

def extract_json_array(text: str) -> list:
    """Extract JSON array from text with improved error handling"""
    try:
        # Try to find JSON array pattern
        match = re.search(r'\[(.*?)\]', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        
        # Try to find comma-separated files
        files = re.findall(r'["\'](.*?)["\']', text)
        if files:
            return [f.strip() for f in files]
            
        # If no JSON array or quotes found, split by commas/newlines
        potential_files = [x.strip() for x in re.split(r'[,\n]', text)]
        return [f for f in potential_files if f and not f.startswith('[') and not f.endswith(']')]
            
    except json.JSONDecodeError:
        return []

def save_content_to_file(file_path: Path, content: str, file_type: str) -> bool:
    """Save content to file with appropriate formatting and error handling"""
    try:
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Format content based on file type
        if file_type == 'md':
            formatted_content = f"# {file_path.stem}\n\n{content}"
        elif file_type in ['py', 'sql']:
            formatted_content = f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}"
        elif file_type in ['yaml', 'yml']:
            formatted_content = f"# Generated configuration\n# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}"
        else:
            formatted_content = content

        # Write content to file with appropriate encoding
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(formatted_content)
            f.flush()  # Ensure content is written to disk
            os.fsync(f.fileno())  # Force flush to disk
        
        return True
    except Exception as e:
        print(f"Error saving file {file_path}: {str(e)}")
        return False

def generate_related_files(subtask: SubtaskRequest, base_content: str) -> dict:
    """Generate related files based on subtask type and description"""
    project_dir = Path(sanitize_project_name(subtask.project_name))
    stage_dir = project_dir / sanitize_project_name(subtask.title)
    files_created = []

    # File generation prompt
    prompt = f"""
    Based on this task:
    Title: {subtask.title}
    Description: {subtask.description}
    Implementation Details: {subtask.how_to_build}
    
    Original Documentation:
    {base_content}

    Generate the necessary implementation files. For each file, provide:
    1. The file name with appropriate extension
    2. The complete file content
    
    Format your response as:
    [FILE: filename.ext]
    content...
    [END FILE]
    [FILE: another_file.ext]
    content...
    [END FILE]

    Include appropriate files based on the stage:
    - Requirements stage: Use .md, .yaml files
    - Design stage: Use .puml (PlantUML), .sql, .yaml files
    - Implementation: Use .py, .js, .ts, .java files
    - Testing: Use _test.py, .spec.js files
    - Deployment: Use Dockerfile, docker-compose.yml, .conf files
    - Maintenance: Use .sh, .bat, monitoring configs
    
    Ensure each file follows best practices and includes:
    - Proper documentation
    - Error handling
    - Logging where appropriate
    - Configuration options
    - Security considerations
    """
    
    try:
        # Get file suggestions from LLM
        response = make_llm_call(
            messages=[{"role": "user", "content": prompt}],
            model=DEFAULT_MODEL,
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse response and create files
        file_blocks = re.findall(r'\[FILE: (.*?)\](.*?)\[END FILE\]', 
                               response, re.DOTALL)
        
        for filename, content in file_blocks:
            filename = filename.strip()
            content = content.strip()
            file_path = stage_dir / filename
            
            # Get file extension
            file_ext = Path(filename).suffix.lstrip('.')
            
            # Save the file
            if save_content_to_file(file_path, content, file_ext):
                files_created.append(str(file_path))
        
        return {
            "stage": subtask.title,
            "project_folder": str(project_dir),
            "files_created": files_created,
            "status": "completed"
        }

    except Exception as e:
        print(f"Error generating related files: {str(e)}")
        return {
            "stage": subtask.title,
            "error": str(e),
            "status": "failed"
        }

# Modify execute_subtask to include related files generation
def execute_subtask(request: SubtaskRequest):
    """Execute subtask with improved file handling and required files check"""
    
    def check_required_files(project_dir: Path, required_files: list) -> tuple[bool, list, list]:
        """Check for required files and create placeholders if needed"""
        missing_files = []
        created_files = []
        
        for file in required_files:
            if not file:  # Skip empty strings
                continue
            file_path = project_dir / file.strip()
            
            if not file_path.exists():
                # Create placeholder files with template content
                template_content = generate_template_content(file, request)
                if save_content_to_file(file_path, template_content, file_path.suffix[1:]):
                    created_files.append(str(file_path))
                else:
                    missing_files.append(file)
                    
        return len(missing_files) == 0, missing_files, created_files

    # Modified prompt to get clearer file list
    prompt = f"""
    Based on this task, list only the input files needed before implementation.
    Return ONLY a JSON array of filenames, nothing else.
    
    Task: {request.title}
    Description: {request.description}
    
    Example format:
    ["config.yaml", "schema.sql", "requirements.txt"]
    """

    try:
        # Get required files list
        files_response = make_llm_call(
            messages=[{"role": "user", "content": prompt}],
            model=DEFAULT_MODEL,  # Updated from hardcoded model name
            temperature=0.2,
            max_tokens=500
        )
        
        # Parse required files with improved handling
        files_response = files_response.strip()
        required_files = extract_json_array(files_response)
        
        # Log the response and parsed files for debugging
        print(f"Files response: {files_response}")
        print(f"Parsed required files: {required_files}")
        
        # Check if required files exist
        project_dir = Path(sanitize_project_name(request.project_name))
        files_exist, missing_files, created_files = check_required_files(project_dir, required_files)
        
        if created_files:
            print(f"Created placeholder files: {', '.join(created_files)}")
        
        if not files_exist:
            return {
                "stage": request.title,
                "status": "warning",
                "message": f"Created placeholder files for: {', '.join(created_files)}",
                "missing_files": missing_files,
                "project_folder": str(project_dir),
                "files_created": created_files
            }

        # Continue with existing implementation
        implementation_prompt = f"""
        You are the {request.Agent_Name} working on:
        
        Project: {request.project_name}
        Task ID: {request.id}
        Title: {request.title}
        Description: {request.description}
        
        Additional Implementation Guidelines:
        {request.how_to_build}
        
        Required Files Present:
        {', '.join(required_files)}
        
        Create a detailed markdown document that includes all necessary information, code, diagrams, and specifications.
        Focus on production-ready, maintainable, and secure solutions.
        Format your response in clear sections with proper markdown headings.
        """

        # Main implementation call
        output = make_llm_call(
            messages=[{"role": "user", "content": implementation_prompt}],
            model=DEFAULT_MODEL,  # Updated from hardcoded model name
            temperature=0.3,
            max_tokens=2000
        )
        
        output = output.strip()
        stage_dir = project_dir / sanitize_project_name(request.title)
        file_path = stage_dir / f"{sanitize_project_name(request.title)}.md"
        
        if save_content_to_file(file_path, output, 'md'):
            related_files_result = generate_related_files(request, output)
            
            return {
                "stage": request.title,
                "project_folder": str(project_dir),
                "files_created": [str(file_path)] + related_files_result.get("files_created", []),
                "required_files_checked": required_files,
                "status": "completed"
            }
        else:
            raise Exception("Failed to save output file")

    except RateLimitError as e:
        print(f"Rate limit error: {str(e)}")
        return {
            "stage": request.title,
            "status": "terminated",
            "error": "Rate limit reached. Process terminated.",
            "retry": False
        }
    except Exception as e:
        print(f"Error in execute_subtask: {str(e)}")
        return {
            "stage": request.title,
            "error": str(e),
            "status": "failed"
        }

def generate_template_content(filename: str, request: SubtaskRequest) -> str:
    """Generate template content for different file types"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    base_template = f"# Generated for project: {request.project_name}\n# Created on: {timestamp}\n\n"
    
    if filename.endswith('.md'):
        return f"{base_template}# {Path(filename).stem}\n\n## Overview\n\n## Details\n"
    
    elif filename.endswith('.txt'):
        return f"{base_template}Project: {request.project_name}\nStage: {request.title}\n"
    
    elif filename.endswith('.csv'):
        return "ID,Title,Description,Status,Priority\n"
    
    elif filename.endswith('.docx'):
        return f"{base_template}This is a placeholder for {filename}. Please replace with actual content."
    
    return f"{base_template}Placeholder content for {filename}"

# -----------------------------
# API Endpoints
# -----------------------------
@app.post("/breakdown")
def breakdown_project(request: ProjectRequest):
    prompt = f"""
    As a Technical Project Manager, break down this project into clear, actionable implementation stages:

    Project: {request.project_description}

    For each stage, provide precise, implementation-focused details. Return a JSON array where each object has this structure:
    {{
        "id": "task_number",
        "title": "stage_name",  # Must exactly match one of the predefined stages
        "description": "specific_actionable_tasks",
        "how_to_build": "step_by_step_guide",
        "Agent_Name": "role",
        "required_files": ["file_list"],
        "dependencies": ["dependencies"],
        "acceptance_criteria": ["criteria"]
    }}

    Generate tasks for EXACTLY these stages with these EXACT titles (do not modify these titles):

    1. "Requirements_GatheringAnd_Analysis" (Requirements Analyst)
       - Requirements gathering and documentation
       - User stories and acceptance criteria
       - System specifications analysis

    2. "Design" (System Architect)
       - System architecture design
       - Database schema design
       - API contract specification

    3. "Implementation_Development" (Senior Developer)
       - Core functionality development
       - Integration implementation
       - Code structure organization

    4. "Testing_Quality_Assurance" (QA Engineer)
       - Test planning and scenarios
       - Test automation implementation
       - Performance testing metrics

    5. "Deployment" (DevOps Engineer)
       - Infrastructure configuration
       - Deployment pipeline setup
       - Monitoring implementation

    6. "Maintenance" (SRE)
       - System monitoring setup
       - Backup procedures
       - Update protocol implementation

    Important:
    - Use EXACTLY these titles in the 'title' field of each task
    - Do not modify or reformat the titles
    - Ensure each task title matches its corresponding endpoint
    - Maintain the exact spelling and underscore format

    Make all descriptions:
    - Direct and actionable
    - Technology-specific
    - With measurable outcomes
    - Including clear deliverables

    Format each 'how_to_build' with:
    1. Prerequisites
    2. Step-by-step commands
    3. Code snippets
    4. Configuration examples
    5. Validation steps
    """

    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,  # Changed from lmeta-llama to DEFAULT_MODEL
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2000,
        top_p=0.9,
    )

    response_text = completion.choices[0].message.content
    subtasks = parse_llm_json(response_text)
    return {"project": request.project_description, "subtasks": subtasks}

# -----------------------------
# Endpoints for all SDLC stages
# -----------------------------
@app.post("/Requirements_GatheringAnd_Analysis/")
def Requirements_GatheringAnd_Analysis(request: SubtaskRequest):
    return execute_subtask(request)

@app.post("/Design/")
def Design(request: SubtaskRequest):
    return execute_subtask(request)

@app.post("/Implementation_Development/")
def Implementation_Development(request: SubtaskRequest):
    return execute_subtask(request)

@app.post("/Testing_Quality_Assurance/")
def Testing_Quality_Assurance(request: SubtaskRequest):
    return execute_subtask(request)

@app.post("/Deployment/")
def Deployment(request: SubtaskRequest):
    return execute_subtask(request)

@app.post("/Maintenance/")
def Maintenance(request: SubtaskRequest):
    return execute_subtask(request)

def sanitize_project_name(name: str) -> str:
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

class RateLimitError(Exception):
    """Custom exception for rate limiting"""
    pass

def is_rate_limit_error(exception):
    """Check if the exception is due to rate limiting"""
    return isinstance(exception, RateLimitError) or (
        hasattr(exception, 'error') and 
        getattr(exception.error, 'code', None) == 'rate_limit_exceeded'
    )

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(1),
    retry=retry_if_exception(is_rate_limit_error)
)
def make_llm_call(messages, model=None, temperature=0.3, max_tokens=2000):
    """Make LLM API call with single retry attempt"""
    try:
        # Use the global model if none specified
        model_to_use = model or DEFAULT_MODEL
        
        completion = client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return completion.choices[0].message.content
    except Exception as e:
        if 'rate_limit' in str(e).lower():
            print(f"Rate limit reached. Process terminated.")
            raise RateLimitError("Rate limit reached. Please try again later.")
        raise e
