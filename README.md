# Syncro - AI-Powered Project Management System

Syncro is an intelligent project breakdown and management system that uses AI to decompose complex projects into manageable subtasks across the entire Software Development Life Cycle (SDLC).

## Features

- 🤖 **AI-Powered Breakdown**: Automatically breaks down project descriptions into detailed SDLC stages
- 📋 **Structured Workflow**: Covers Requirements, Design, Implementation, Testing, Deployment, and Maintenance
- 🔄 **Automated Generation**: Creates comprehensive documentation and implementation files for each stage
- 🐳 **Docker-Ready**: Fully containerized with Docker Compose for easy deployment
- 💾 **Persistent Storage**: All generated files are stored locally with Docker volume mounting

## Architecture

### Services
- **Backend (FastAPI)**: Handles project breakdown and file generation using Groq LLM API
- **Frontend (Streamlit)**: Provides an intuitive web interface for project management

### SDLC Stages Covered

1. **Requirements Gathering & Analysis**
   - Requirements documentation
   - User stories and acceptance criteria
   - System specifications

2. **Design**
   - System architecture
   - Database schema
   - API contracts

3. **Implementation & Development**
   - Core functionality
   - Code structure
   - Integration implementation

4. **Testing & Quality Assurance**
   - Test planning
   - Test automation
   - Performance metrics

5. **Deployment**
   - Infrastructure configuration
   - CI/CD pipeline setup
   - Monitoring implementation

6. **Maintenance**
   - System monitoring
   - Backup procedures
   - Update protocols

7. **Execution & Startup**
   - Startup scripts generation (start.sh, start.bat)
   - Running instructions (README_RUN.md)
   - Quick start guide (QUICK_START.md)
   - Environment setup automation

## Prerequisites

- Docker and Docker Compose
- Groq API key (get it from https://console.groq.com/keys)

## Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd Syncro
```

2. **Set up environment variables**

Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

3. **Start the application**
```bash
docker compose up --build
```

4. **Access the application**
   - Frontend UI: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Usage

1. Open the Streamlit frontend at http://localhost:8501
2. Enter your project description in the text area
3. Click "🔍 Breakdown Project" to generate subtasks
4. Review the generated SDLC stages
5. Click "⚡ Build Subtask" for each stage to generate implementation files
6. View and download generated files directly in the UI

## File Storage

All generated files are stored in the `./output` directory on your host machine:

```
./output/
  └── ProjectName_TIMESTAMP/
      ├── Requirements_GatheringAnd_Analysis/
      │   ├── Requirements_GatheringAnd_Analysis.md
      │   └── additional_files...
      ├── Design/
      │   ├── Design.md
      │   └── additional_files...
      ├── Implementation_Development/
      │   └── ...
      ├── Testing_Quality_Assurance/
      │   └── ...
      ├── Deployment/
      │   └── ...
      ├── Maintenance/
      │   └── ...
      └── Execution_And_Startup/
          ├── start.sh              # Unix/Linux/Mac startup script
          ├── start.bat             # Windows startup script
          ├── setup_env.sh          # Unix/Linux/Mac environment setup
          ├── setup_env.bat         # Windows environment setup
          ├── README_RUN.md         # Comprehensive running guide
          ├── QUICK_START.md        # 2-minute quick start
          └── HOW_TO_RUN.md         # Quick reference
```

### File Types Generated

- **Documentation**: `.md`, `.txt`
- **Code**: `.py`, `.js`, `.ts`, `.java`
- **Configuration**: `.yaml`, `.yml`, `.json`, `.env`
- **Database**: `.sql`
- **Deployment**: `Dockerfile`, `docker-compose.yml`
- **Diagrams**: `.puml` (PlantUML)
- **Scripts**: `.sh`, `.bat`

## Configuration

### Environment Variables

- `GROQ_API_KEY`: Your Groq API key (required)
- `DEFAULT_MODEL`: Primary LLM model (default: `llama-3.3-70b-versatile`)
- `BACKUP_MODEL`: Fallback model (default: `deepseek-r1-distill-llama-70b`)

### Docker Volumes

The application uses volume mounting to persist files:
```yaml
volumes:
  - ./output:/sync_space/output
```

This ensures:
- Files persist across container restarts
- Files are accessible from both services
- You can access files directly on your host machine

## API Endpoints

### Project Breakdown
```http
POST /breakdown
Content-Type: application/json

{
  "project_description": "Your project description here"
}
```

### Stage Execution
```http
POST /Requirements_GatheringAnd_Analysis/
POST /Design/
POST /Implementation_Development/
POST /Testing_Quality_Assurance/
POST /Deployment/
POST /Maintenance/
POST /Execution_And_Startup/

Content-Type: application/json

{
  "id": 1,
  "title": "Stage Title",
  "description": "Stage description",
  "how_to_build": "Implementation guidelines",
  "Agent_Name": "Role name",
  "project_name": "ProjectName_TIMESTAMP"
}
```

### Health Check
```http
GET /health
```

## Development

### Running Locally (without Docker)

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Start the backend**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

3. **Start the frontend** (in a separate terminal)
```bash
streamlit run main.py --server.port 8501
```

### Project Structure

```
Syncro/
├── app.py                 # FastAPI backend application
├── main.py               # Streamlit frontend application
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── compose.yaml         # Docker Compose configuration
├── README.md           # This file
├── README.Docker.md    # Docker-specific documentation
├── output/             # Generated files directory
└── .env               # Environment variables (create this)
```

## Technologies Used

- **Backend**: FastAPI, Pydantic, Groq API
- **Frontend**: Streamlit
- **AI/LLM**: Groq (llama-3.3-70b-versatile, deepseek-r1-distill-llama-70b)
- **Containerization**: Docker, Docker Compose
- **Python**: 3.10+

## Troubleshooting

### Files not showing up
1. Check that the `./output` directory exists and has proper permissions
2. Verify the volume mount in `compose.yaml`: `./output:/sync_space/output`
3. Check container logs: `docker compose logs backend` or `docker compose logs frontend`

### API connection errors
1. Verify both containers are running: `docker compose ps`
2. Check that the backend is healthy: http://localhost:8000/health
3. Ensure the frontend can reach the backend at `http://backend:8000`

### Groq API errors
1. Verify your API key is set correctly in `.env`
2. Check your Groq API quota and rate limits
3. Review the backend logs for detailed error messages

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]

## Support

For issues and questions, please open an issue on the GitHub repository.

