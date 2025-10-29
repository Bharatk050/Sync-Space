import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq  # official Groq client
from dotenv import load_dotenv
import json
import re
from pathlib import Path
from datetime import datetime
from time import sleep
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception
from fastapi.middleware.cors import CORSMiddleware

# -----------------------------
# Load API key
# -----------------------------
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=groq_api_key)
app = FastAPI(title="Syncro API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Global Configuration
# -----------------------------
DEFAULT_MODEL = "llama-3.3-70b-versatile"  # Primary model
BACKUP_MODEL = "deepseek-r1-distill-llama-70b"             # Fallback model

# Output directory configuration
OUTPUT_BASE_DIR = Path("/sync_space/output")  # Docker volume mount path
OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

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
def ensure_all_stages(subtasks):
    """Ensure all 7 required stages are present in subtasks"""
    required_stages = [
        {
            "id": "task_1",
            "title": "Requirements_GatheringAnd_Analysis",
            "description": "Gather and analyze project requirements, create user stories, and define acceptance criteria",
            "how_to_build": "1. Analyze project description\n2. Create user stories\n3. Define functional and non-functional requirements\n4. Document acceptance criteria",
            "Agent_Name": "Requirements Analyst"
        },
        {
            "id": "task_2",
            "title": "Design",
            "description": "Design system architecture, database schema, and API contracts",
            "how_to_build": "1. Create system architecture diagrams\n2. Design database schema\n3. Define API contracts and endpoints\n4. Document design decisions",
            "Agent_Name": "System Architect"
        },
        {
            "id": "task_3",
            "title": "Implementation_Development",
            "description": "Develop core functionality and implement the system",
            "how_to_build": "1. Set up development environment\n2. Implement core features\n3. Write clean, maintainable code\n4. Follow design specifications",
            "Agent_Name": "Senior Developer"
        },
        {
            "id": "task_4",
            "title": "Testing_Quality_Assurance",
            "description": "Create test plans, implement tests, and ensure quality",
            "how_to_build": "1. Create test plan\n2. Write unit tests\n3. Implement integration tests\n4. Perform quality assurance",
            "Agent_Name": "QA Engineer"
        },
        {
            "id": "task_5",
            "title": "Deployment",
            "description": "Configure infrastructure and deployment pipeline",
            "how_to_build": "1. Set up infrastructure\n2. Configure deployment pipeline\n3. Create Docker configurations\n4. Set up monitoring",
            "Agent_Name": "DevOps Engineer"
        },
        {
            "id": "task_6",
            "title": "Maintenance",
            "description": "Set up monitoring, backup procedures, and update protocols",
            "how_to_build": "1. Implement monitoring\n2. Create backup procedures\n3. Document update protocols\n4. Set up alerting",
            "Agent_Name": "SRE"
        },
        {
            "id": "task_7",
            "title": "Execution_And_Startup",
            "description": "Generate startup scripts and running instructions for the application",
            "how_to_build": "1. Create start.sh and start.bat scripts\n2. Generate README_RUN.md with instructions\n3. Create setup_env scripts\n4. Write QUICK_START.md guide",
            "Agent_Name": "DevOps Engineer"
        }
    ]
    
    # Get existing stage titles
    existing_titles = {task.get("title") for task in subtasks if task.get("title")}
    
    # Add missing stages
    result = list(subtasks)  # Copy existing tasks
    for required_stage in required_stages:
        if required_stage["title"] not in existing_titles:
            result.append(required_stage)
    
    # Sort by task ID to maintain order
    result.sort(key=lambda x: int(str(x.get("id", "0")).replace("task_", "").replace("error_", "999")))
    
    return result

def parse_llm_json(response_text):
    """Extract JSON from LLM response with improved error handling"""
    try:
        # Clean the response text
        # Remove markdown code blocks
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # Remove comments (// and /* */)
        response_text = re.sub(r'//.*?\n', '\n', response_text)
        response_text = re.sub(r'/\*.*?\*/', '', response_text, flags=re.DOTALL)
        
        # Remove trailing commas before closing braces/brackets
        response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
        
        # First attempt: Try direct JSON parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Second attempt: Try to find a complete JSON array
        match = re.search(r'\[\s*\{.*?\}\s*\]', response_text, re.DOTALL)
        if match:
            json_text = match.group(0)
            # Clean again
            json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
            return json.loads(json_text)
            
        # Third attempt: Try to extract individual JSON objects
        objects = re.findall(r'\{\s*"id".*?\}(?=\s*[,\]])', response_text, re.DOTALL)
        if objects:
            json_array = f"[{','.join(objects)}]"
            json_array = re.sub(r',(\s*[}\]])', r'\1', json_array)
            return json.loads(json_array)
            
        # Fourth attempt: Basic structure extraction
        subtasks = []
        matches = re.finditer(r'"id"\s*:\s*"(\d+)".*?"title"\s*:\s*"([^"]+)".*?"description"\s*:\s*"([^"]+)".*?"Agent_Name"\s*:\s*"([^"]+)"', response_text, re.DOTALL)
        
        for match in matches:
            subtask = {
                "id": match.group(1),
                "title": match.group(2),
                "description": match.group(3),
                "how_to_build": "See detailed implementation guide",
                "Agent_Name": match.group(4)
            }
            subtasks.append(subtask)
            
        if subtasks:
            return subtasks
            
        # Fallback: Return error task
        return [{
            "id": "error_1",
            "title": "Requirements_GatheringAnd_Analysis",
            "description": "Error parsing LLM response. Please try again.",
            "how_to_build": response_text[:200] + "...",
            "Agent_Name": "System"
        }]
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return [{
            "id": "error_2",
            "title": "Requirements_GatheringAnd_Analysis",
            "description": f"JSON parsing error: {str(e)}",
            "how_to_build": "Please try again",
            "Agent_Name": "System"
        }]
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return [{
            "id": "error_3",
            "title": "Requirements_GatheringAnd_Analysis",
            "description": f"Unexpected error: {str(e)}",
            "how_to_build": "Please try again",
            "Agent_Name": "System"
        }]

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

def generate_execution_fallback_files(stage_dir: Path, project_dir: Path, previous_stage_data: dict) -> list:
    """Generate essential execution files as fallback"""
    files_created = []
    
    # Try to detect entry point
    entry_point = "app.py"  # default
    for file_path in previous_stage_data.get('files', {}).keys():
        if 'main.py' in str(file_path).lower():
            entry_point = "main.py"
            break
        elif 'app.py' in str(file_path).lower():
            entry_point = "app.py"
            break
        elif 'index.js' in str(file_path).lower():
            entry_point = "index.js"
            break
    
    # Generate start.sh
    start_sh_content = f"""#!/bin/bash
# Auto-generated startup script

echo "Starting application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the application
echo "Launching {entry_point}..."
python {entry_point}
"""
    
    # Generate start.bat
    start_bat_content = f"""@echo off
REM Auto-generated startup script for Windows

echo Starting application...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\\Scripts\\activate.bat

REM Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start the application
echo Launching {entry_point}...
python {entry_point}
"""
    
    # Detect project language/framework from previous stages
    project_type = "python"  # default
    install_cmd = "pip install -r requirements.txt"
    run_cmd = f"python {entry_point}"
    
    for file_path in previous_stage_data.get('files', {}).keys():
        if 'package.json' in str(file_path).lower():
            project_type = "nodejs"
            install_cmd = "npm install"
            run_cmd = "npm start"
            break
        elif 'pom.xml' in str(file_path).lower():
            project_type = "java"
            install_cmd = "mvn install"
            run_cmd = "mvn spring-boot:run"
            break
    
    # Generate README_RUN.md
    readme_content = f"""# How to Run This Project

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚀 Quick Start (Recommended)

### For {project_type.upper()} Project

**On Unix/Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**On Windows:**
```batch
start.bat
```

The startup script will automatically:
- ✅ Check for dependencies
- ✅ Set up the environment
- ✅ Install required packages
- ✅ Launch the application

---

## 📋 Manual Setup (Alternative)

If you prefer to set up manually, follow these steps:

### Step 1: Verify Prerequisites

Ensure you have the following installed:
- Python 3.8+ (check with `python --version`)
- pip package manager
- Virtual environment support

### Step 2: Create Virtual Environment

```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**On Unix/Linux/Mac:**
```bash
source venv/bin/activate
```

**On Windows (Command Prompt):**
```batch
venv\\Scripts\\activate.bat
```

**On Windows (PowerShell):**
```powershell
venv\\Scripts\\Activate.ps1
```

### Step 4: Install Dependencies

```bash
{install_cmd}
```

### Step 5: Run the Application

```bash
{run_cmd}
```

---

## 🐳 Docker Deployment (Recommended for Production)

If Docker configuration is available in the `Deployment/` directory:

```bash
# Build the image
docker build -t project-name .

# Run the container
docker run -p 8000:8000 project-name

# Or use docker-compose
docker-compose up -d
```

---

## 🔧 Configuration

### Environment Variables

Check the `Deployment/` directory for `.env.example` or configuration files.

Common environment variables:
```bash
export APP_ENV=production
export PORT=8000
export DATABASE_URL=your_database_url
```

### Database Setup

If the project uses a database, check:
- `Design/database_schema.sql` for schema
- `Design/` directory for database configuration

To initialize the database:
```bash
# For PostgreSQL/MySQL
psql -U username -d database_name -f Design/database_schema.sql

# For SQLite
sqlite3 database.db < Design/database_schema.sql
```

---

## 📁 Project Structure

```
project_root/
├── Requirements_GatheringAnd_Analysis/  # Project requirements and specs
├── Design/                               # Architecture and database design
├── Implementation_Development/           # Source code ({entry_point})
├── Testing_Quality_Assurance/            # Test suites
├── Deployment/                           # Docker, CI/CD configs
├── Maintenance/                          # Monitoring and backup scripts
└── Execution_And_Startup/                # Startup scripts (you are here!)
```

---

## 🐛 Troubleshooting

### Issue: "Permission denied" (Unix/Linux/Mac)
**Solution:** Make the script executable:
```bash
chmod +x start.sh
```

### Issue: "Python not found"
**Solutions:**
1. Ensure Python is installed: `python --version`
2. Try using `python3` instead of `python`
3. Add Python to your PATH environment variable

### Issue: "Module not found" or "ImportError"
**Solutions:**
1. Activate virtual environment first
2. Install dependencies: `{install_cmd}`
3. Check `requirements.txt` exists in project root

### Issue: "Port already in use"
**Solution:** Change the port in configuration or kill the process:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Issue: "Database connection error"
**Solutions:**
1. Check database is running
2. Verify DATABASE_URL in environment variables
3. Run database initialization script
4. Check credentials and permissions

---

## 📚 Additional Documentation

For detailed information about each stage:

- **Requirements:** See `Requirements_GatheringAnd_Analysis/` for user stories and acceptance criteria
- **Architecture:** See `Design/` for system design and database schema
- **Implementation:** See `Implementation_Development/` for source code documentation
- **Testing:** See `Testing_Quality_Assurance/` for test plans and reports
- **Deployment:** See `Deployment/` for infrastructure and deployment guides
- **Maintenance:** See `Maintenance/` for monitoring and backup procedures

---

## 💡 Tips

1. **Always use a virtual environment** to avoid dependency conflicts
2. **Check all README files** in each stage directory for specific instructions
3. **Review environment variables** before running in production
4. **Run tests** before deployment: check `Testing_Quality_Assurance/` directory
5. **Backup data** regularly using scripts in `Maintenance/` directory

---

## 🆘 Need Help?

1. Check the documentation in each stage directory
2. Review the `project_info.json` file for project metadata
3. Look at `Testing_Quality_Assurance/` for test examples
4. Consult `Deployment/` for production deployment guides

---

## 📝 Notes

- Entry Point: `{entry_point}`
- Project Type: {project_type.upper()}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Enjoy your project! 🎉
"""
    
    # Generate QUICK_START.md
    quickstart_content = f"""# ⚡ Quick Start Guide

Get up and running in **2 minutes**!

## 🎯 One-Command Start

### On Unix/Linux/Mac:
```bash
chmod +x start.sh && ./start.sh
```

### On Windows:
```batch
start.bat
```

That's it! 🎉 Your application should now be running.

---

## 📍 What Happens Next?

The startup script will:

1. ✅ Check for Python installation
2. ✅ Create a virtual environment (if needed)
3. ✅ Activate the environment
4. ✅ Install all dependencies from `requirements.txt`
5. ✅ Launch **{entry_point}**

---

## 🌐 Access Your Application

After startup completes, access your application at:

- **Local:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (if FastAPI)
- **Admin:** Check console output for specific URLs

---

## 🛑 Stop the Application

Press `Ctrl + C` in the terminal to stop the application.

---

## 📖 Need More Details?

For detailed setup instructions, troubleshooting, and configuration:

👉 See **README_RUN.md** in this directory

---

## 🔧 Common First Steps

### Check if it's running:
```bash
curl http://localhost:8000
```

### View logs:
Check the console output where you ran the start script.

### Run tests:
```bash
# Activate venv first
source venv/bin/activate  # Unix/Linux/Mac
# OR
venv\\Scripts\\activate.bat  # Windows

# Run tests
pytest  # or the test command for your project
```

---

**Project:** {project_dir.name if project_dir else 'Unknown'}  
**Entry Point:** `{entry_point}`  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # Generate setup_env.sh
    setup_env_sh = f"""#!/bin/bash
# Environment setup script for Unix/Linux/Mac

echo "🔧 Setting up environment for {project_dir.name if project_dir else 'project'}..."

# Check Python version
python_version=$(python3 --version 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ Python found: $python_version"
else
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "📥 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "⚠️  No requirements.txt found"
fi

# Check for .env file
if [ ! -f ".env" ] && [ -f "Deployment/.env.example" ]; then
    echo "⚠️  No .env file found. Copy from Deployment/.env.example and configure:"
    echo "   cp Deployment/.env.example .env"
fi

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "To activate the virtual environment manually, run:"
echo "   source venv/bin/activate"
echo ""
echo "To run the application:"
echo "   {run_cmd}"
"""

    # Generate setup_env.bat
    setup_env_bat = f"""@echo off
REM Environment setup script for Windows

echo 🔧 Setting up environment for {project_dir.name if project_dir else 'project'}...

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8 or higher.
    exit /b 1
)
echo ✅ Python found

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\\Scripts\\activate.bat

REM Upgrade pip
echo 📦 Upgrading pip...
pip install --upgrade pip --quiet

REM Install dependencies
if exist "requirements.txt" (
    echo 📥 Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    echo ✅ Dependencies installed
) else (
    echo ⚠️  No requirements.txt found
)

REM Check for .env file
if not exist ".env" (
    if exist "Deployment\\.env.example" (
        echo ⚠️  No .env file found. Copy from Deployment\\.env.example and configure:
        echo    copy Deployment\\.env.example .env
    )
)

echo.
echo ✅ Environment setup complete!
echo.
echo To activate the virtual environment manually, run:
echo    venv\\Scripts\\activate.bat
echo.
echo To run the application:
echo    {run_cmd}

pause
"""

    # Generate HOW_TO_RUN.md (alias for README_RUN.md for better discoverability)
    how_to_run_content = f"""# HOW TO RUN - {project_dir.name if project_dir else 'Project'}

> 📌 This is a reference to the main running instructions.

For complete instructions on how to run this project, see:

👉 **[README_RUN.md](./README_RUN.md)**

## Quick Commands

**Start the application:**
```bash
# Unix/Linux/Mac
./start.sh

# Windows
start.bat
```

**Setup environment only:**
```bash
# Unix/Linux/Mac
./setup_env.sh

# Windows
setup_env.bat
```

**Manual start:**
```bash
# Activate venv
source venv/bin/activate  # Unix/Linux/Mac
venv\\Scripts\\activate.bat  # Windows

# Run
{run_cmd}
```

---

**Entry Point:** `{entry_point}`  
**Project Type:** {project_type.upper()}  
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # Save files
    try:
        start_sh_path = stage_dir / "start.sh"
        if save_content_to_file(start_sh_path, start_sh_content, 'sh'):
            files_created.append(str(start_sh_path))
            # Make executable on Unix-like systems
            try:
                import stat
                os.chmod(start_sh_path, os.stat(start_sh_path).st_mode | stat.S_IEXEC)
            except Exception:
                pass
        
        start_bat_path = stage_dir / "start.bat"
        if save_content_to_file(start_bat_path, start_bat_content, 'bat'):
            files_created.append(str(start_bat_path))
        
        readme_path = stage_dir / "README_RUN.md"
        if save_content_to_file(readme_path, readme_content, 'md'):
            files_created.append(str(readme_path))
        
        quickstart_path = stage_dir / "QUICK_START.md"
        if save_content_to_file(quickstart_path, quickstart_content, 'md'):
            files_created.append(str(quickstart_path))
        
        how_to_run_path = stage_dir / "HOW_TO_RUN.md"
        if save_content_to_file(how_to_run_path, how_to_run_content, 'md'):
            files_created.append(str(how_to_run_path))
        
        setup_sh_path = stage_dir / "setup_env.sh"
        if save_content_to_file(setup_sh_path, setup_env_sh, 'sh'):
            files_created.append(str(setup_sh_path))
            # Make executable
            try:
                import stat
                os.chmod(setup_sh_path, os.stat(setup_sh_path).st_mode | stat.S_IEXEC)
            except Exception:
                pass
        
        setup_bat_path = stage_dir / "setup_env.bat"
        if save_content_to_file(setup_bat_path, setup_env_bat, 'bat'):
            files_created.append(str(setup_bat_path))
            
    except Exception as e:
        print(f"Error creating fallback files: {str(e)}")
    
    return files_created

def generate_related_files(subtask: SubtaskRequest, base_content: str) -> dict:
    """Generate related files based on subtask type and description"""
    project_dir = OUTPUT_BASE_DIR / sanitize_project_name(subtask.project_name)
    stage_dir = project_dir / sanitize_project_name(subtask.title)
    files_created = []

    # Collect previous stage files
    previous_stage_data = collect_previous_stage_files(project_dir, subtask.title)
    
    # Build context from previous files
    previous_files_context = ""
    if previous_stage_data['count'] > 0:
        previous_files_context = f"""
    
    PREVIOUS STAGE FILES TO BUILD UPON:
    {previous_stage_data['summary']}
    
    Key Previous File Contents:
    """
        # Include key previous files
        for file_path, content in list(previous_stage_data['files'].items())[:3]:
            previous_files_context += f"\n--- {file_path} ---\n{content[:1500]}\n"
            if len(content) > 1500:
                previous_files_context += "[... truncated ...]\n"

    # Special handling for Execution_And_Startup stage
    execution_specific_instructions = ""
    if subtask.title == "Execution_And_Startup":
        execution_specific_instructions = """
    
    FOR EXECUTION_AND_STARTUP STAGE - MANDATORY FILES TO GENERATE:
    
    You MUST generate these files:
    1. start.sh - Bash script to start the application on Unix/Linux/Mac
    2. start.bat - Batch script to start the application on Windows
    3. run.py - Cross-platform Python script to run the application
    4. setup_env.sh - Environment setup script for Unix/Linux/Mac
    5. setup_env.bat - Environment setup script for Windows
    6. README_RUN.md - Comprehensive guide on how to run the application
    7. QUICK_START.md - Quick start guide (1-2 minute setup)
    
    Analyze the previous stage files to determine:
    - Entry point: Look in Implementation_Development for main.py, app.py, index.js, etc.
    - Dependencies: Check requirements.txt, package.json, Dockerfile
    - Database: Check Design/database_schema.sql for DB initialization
    - Ports: Check Deployment files for port configurations
    - Environment variables: Check Deployment/.env or docker-compose.yml
    
    Make the scripts ACTUALLY WORK with the specific project files generated.
    Use real file names, real commands, and real configuration from previous stages.
    """

    # File generation prompt
    prompt = f"""
    Based on this task:
    Title: {subtask.title}
    Description: {subtask.description}
    Implementation Details: {subtask.how_to_build}
    
    Original Documentation:
    {base_content}
    {previous_files_context}
    {execution_specific_instructions}

    CRITICAL INSTRUCTIONS:
    - Review and reference the previous stage files listed above
    - Ensure consistency with naming conventions, schemas, and APIs from previous stages
    - Build implementations that work with the existing structure
    - Use actual values and names from previous documents (e.g., database schema, API endpoints)
    
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
    - Requirements_GatheringAnd_Analysis: Use .md, .yaml, .txt files for requirements and user stories
    - Design: Use .puml (PlantUML), .sql, .yaml files for architecture and schemas
    - Implementation_Development: Use .py, .js, .ts, .java files for actual code implementation
    - Testing_Quality_Assurance: Use _test.py, .spec.js, test_*.py files for test suites
    - Deployment: Use Dockerfile, docker-compose.yml, .conf, .sh files for deployment
    - Maintenance: Use .sh, .bat, monitoring configs, backup scripts
    - Execution_And_Startup: Use start.sh, start.bat, run.py, README_RUN.md, setup_env.sh, QUICK_START.md
    
    Ensure each file follows best practices and includes:
    - Proper documentation
    - Error handling
    - Logging where appropriate
    - Configuration options
    - Security considerations
    - REFERENCES to previous stage artifacts (schemas, APIs, requirements)
    """
    
    try:
        # Adjust max_tokens based on stage
        max_tokens = 4000 if subtask.title == "Execution_And_Startup" else 2000
        
        # Get file suggestions from LLM
        response = make_llm_call(
            messages=[{"role": "user", "content": prompt}],
            model=DEFAULT_MODEL,
            temperature=0.3,
            max_tokens=max_tokens
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
        
        # Fallback: Ensure critical files exist for Execution_And_Startup
        if subtask.title == "Execution_And_Startup" and len(files_created) < 3:
            files_created.extend(generate_execution_fallback_files(
                stage_dir, project_dir, previous_stage_data
            ))
        
        return {
            "stage": subtask.title,
            "project_folder": str(project_dir),
            "files_created": files_created,
            "status": "completed"
        }

    except Exception as e:
        print(f"Error generating related files: {str(e)}")
        
        # Try fallback for Execution_And_Startup even on error
        if subtask.title == "Execution_And_Startup":
            try:
                print("Attempting fallback file generation for Execution_And_Startup...")
                fallback_files = generate_execution_fallback_files(
                    stage_dir, project_dir, previous_stage_data
                )
                if fallback_files:
                    return {
                        "stage": subtask.title,
                        "project_folder": str(project_dir),
                        "files_created": fallback_files,
                        "status": "completed_with_fallback",
                        "warning": f"Used fallback generation due to error: {str(e)}"
                    }
            except Exception as fallback_error:
                print(f"Fallback also failed: {str(fallback_error)}")
        
        return {
            "stage": subtask.title,
            "error": str(e),
            "status": "failed"
        }

# Modify execute_subtask to include related files generation
def collect_previous_stage_files(project_dir: Path, current_stage: str) -> dict:
    """Collect files and their contents from previous stages"""
    stage_order = [
        "Requirements_GatheringAnd_Analysis",
        "Design",
        "Implementation_Development",
        "Testing_Quality_Assurance",
        "Deployment",
        "Maintenance",
        "Execution_And_Startup"
    ]
    
    try:
        current_index = stage_order.index(current_stage)
    except ValueError:
        current_index = 0
    
    previous_files = {}
    file_summaries = []
    
    # Collect files from all previous stages
    for stage in stage_order[:current_index]:
        stage_dir = project_dir / sanitize_project_name(stage)
        if stage_dir.exists():
            for file_path in stage_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        # Read file content for text files
                        if file_path.suffix in ['.md', '.txt', '.py', '.sql', '.yaml', '.yml', '.json', '.puml']:
                            content = file_path.read_text(encoding='utf-8')
                            relative_path = file_path.relative_to(project_dir)
                            previous_files[str(relative_path)] = content
                            
                            # Create summary for prompt
                            file_summaries.append(f"- {relative_path} ({len(content)} chars)")
                    except Exception as e:
                        print(f"Could not read file {file_path}: {str(e)}")
    
    return {
        "files": previous_files,
        "summary": "\n".join(file_summaries) if file_summaries else "No previous files found",
        "count": len(previous_files)
    }

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
        project_dir = OUTPUT_BASE_DIR / sanitize_project_name(request.project_name)
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

        # Collect previous stage files and content
        previous_stage_data = collect_previous_stage_files(project_dir, request.title)
        
        # Build context from previous files
        previous_context = ""
        if previous_stage_data['count'] > 0:
            previous_context = f"""
        
        IMPORTANT: Previous Stage Files Available ({previous_stage_data['count']} files):
        {previous_stage_data['summary']}
        
        Previous Stage Content to Build Upon:
        """
            # Include key file contents (limit to most important ones)
            for file_path, content in list(previous_stage_data['files'].items())[:5]:  # Limit to 5 files to avoid token overflow
                previous_context += f"\n\n--- Content of {file_path} ---\n{content[:2000]}\n"  # Limit content to 2000 chars per file
                if len(content) > 2000:
                    previous_context += "\n[... content truncated ...]\n"

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
        {previous_context}
        
        CRITICAL: Build upon the previous stage files listed above. Reference and use the content from previous stages to ensure continuity and consistency.
        Make sure your implementation:
        1. Aligns with requirements from previous stages
        2. Uses the same naming conventions and structure
        3. References specific details from previous documents
        4. Ensures the final project folder will work as a cohesive whole
        
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
            
            # Save metadata about stage dependencies
            metadata = {
                "stage": request.title,
                "timestamp": datetime.now().isoformat(),
                "previous_files_referenced": list(previous_stage_data['files'].keys()),
                "previous_files_count": previous_stage_data['count'],
                "files_generated": [str(file_path)] + related_files_result.get("files_created", [])
            }
            
            metadata_file = stage_dir / "stage_metadata.json"
            try:
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                print(f"Failed to save metadata: {str(e)}")
            
            return {
                "stage": request.title,
                "project_folder": str(project_dir),
                "files_created": [str(file_path)] + related_files_result.get("files_created", []),
                "required_files_checked": required_files,
                "previous_files_referenced": list(previous_stage_data['files'].keys())[:10],  # Limit to first 10 for display
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

    7. "Execution_And_Startup" (DevOps Engineer)
       - Startup scripts creation
       - Running instructions
       - Quick start guide
       - Environment setup automation

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

    try:
        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000,
            top_p=0.9,
        )

        response_text = completion.choices[0].message.content
        subtasks = parse_llm_json(response_text)
        
        # Ensure all 7 stages are present
        subtasks = ensure_all_stages(subtasks)
        
        print(f"Breakdown complete: {len(subtasks)} stages generated")
        
        return {"project": request.project_description, "subtasks": subtasks}
        
    except Exception as e:
        print(f"Error in breakdown: {str(e)}")
        # Return all stages with default descriptions as fallback
        return {
            "project": request.project_description,
            "subtasks": ensure_all_stages([])
        }

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

@app.post("/Execution_And_Startup/")
def Execution_And_Startup(request: SubtaskRequest):
    return execute_subtask(request)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Syncro API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        return "Unnamed_Project"
        
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
