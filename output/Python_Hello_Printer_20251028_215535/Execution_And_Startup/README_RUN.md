# README_RUN

# How to Run This Project

## Quick Start

### Option 1: Using Startup Script (Recommended)

**On Unix/Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**On Windows:**
```batch
start.bat
```

### Option 2: Manual Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
```bash
# On Unix/Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate.bat
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment support

## Troubleshooting

### Issue: "Permission denied"
**Solution:** Make the script executable:
```bash
chmod +x start.sh
```

### Issue: "Python not found"
**Solution:** Ensure Python is installed and in your PATH

### Issue: "Module not found"
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

See the following directories for more information:
- `Requirements_GatheringAnd_Analysis/` - Project requirements
- `Design/` - System architecture and design
- `Implementation_Development/` - Source code
- `Testing_Quality_Assurance/` - Test suites
- `Deployment/` - Deployment configurations
- `Maintenance/` - Maintenance procedures

## Need Help?

Refer to the documentation in each stage directory for detailed information.
