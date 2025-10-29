# Quick Reference: Stage Continuity Features

## What's New? 🎉

Your project generation system now ensures that **each stage builds upon previous stages**, creating a cohesive, working project.

## How It Works 🔄

### Before (Old Behavior)
```
Requirements → [Independent files]
Design       → [Independent files]
Implementation → [Independent files]
❌ No connection between stages
❌ Inconsistent naming and structures
❌ Final project may not work together
```

### After (New Behavior)
```
Requirements → [requirements.md, user_stories.xlsx]
                    ↓ (reads and references)
Design       → [design.md, schema.sql, api.yaml]
                    ↓ (reads and references)
Implementation → [app.py, models.py, routes.py]
                    ↓ (reads and references)
Testing      → [test_app.py, test_api.py]
✅ Each stage knows about previous stages
✅ Consistent naming and structures
✅ Final project works as a whole
```

## What You'll See 👀

### 1. **Stage Dependency Information**
When building a stage, you'll see:
```
ℹ️ This stage will build upon: Requirements_GatheringAnd_Analysis, Design
```

### 2. **Success with Context**
After successful generation:
```
✅ Subtask completed successfully!

🔗 Previous Stage Files Used
- Requirements_GatheringAnd_Analysis/requirements.md
- Requirements_GatheringAnd_Analysis/user_stories.xlsx
- Design/design_document.md
- Design/database_schema.sql
Total: 4 files referenced
```

### 3. **Stage Metadata Files**
Each stage folder now contains `stage_metadata.json`:
```json
{
  "stage": "Implementation_Development",
  "timestamp": "2025-10-28T21:35:10",
  "previous_files_referenced": [
    "Requirements_GatheringAnd_Analysis/requirements.md",
    "Design/database_schema.sql",
    "Design/api_contract.yaml"
  ],
  "previous_files_count": 3,
  "files_generated": [
    "Implementation_Development/app.py",
    "Implementation_Development/models.py"
  ]
}
```

## Usage Tips 💡

### Best Practices

1. **Build Stages in Order**
   - Always complete Requirements before Design
   - Complete Design before Implementation
   - Follow the natural SDLC progression

2. **Review Previous Files**
   - Check the "Previous Stage Files Used" section
   - Verify the right context was used
   - Confirm consistency across stages

3. **Use Metadata for Debugging**
   - Check `stage_metadata.json` if something seems wrong
   - Verify which files were referenced
   - Confirm the timestamp of generation

### Common Scenarios

#### Scenario 1: Starting a New Project
```
1. Generate Requirements → Creates requirements.md
2. Generate Design → Uses requirements.md to create schema.sql
3. Generate Implementation → Uses requirements.md + schema.sql to create app.py
✅ Everything is connected!
```

#### Scenario 2: Regenerating a Stage
```
1. If you regenerate Design, it will still use Requirements
2. If you regenerate Implementation, it will use the latest Design files
3. If you regenerate Testing, it will use the latest Implementation files
✅ Always uses most recent previous stage files!
```

#### Scenario 3: Checking Consistency
```
1. Look at Design/stage_metadata.json
2. Verify it referenced Requirements files
3. Look at Implementation/stage_metadata.json
4. Verify it referenced both Requirements and Design files
✅ Audit trail for full traceability!
```

## Technical Details 🔧

### What Files Are Referenced?
- `.md` (Markdown documentation)
- `.txt` (Text files)
- `.py` (Python code)
- `.sql` (Database schemas)
- `.yaml`/`.yml` (Configuration files)
- `.json` (Data files)
- `.puml` (PlantUML diagrams)

### How Much Context Is Used?
- **Up to 5 files** from previous stages (main prompt)
- **Up to 2000 characters** per file (to avoid token limits)
- **Most recent content** is always used
- **Smart truncation** if files are large

### Stage Order
1. `Requirements_GatheringAnd_Analysis`
2. `Design`
3. `Implementation_Development`
4. `Testing_Quality_Assurance`
5. `Deployment`
6. `Maintenance`
7. `Execution_And_Startup` ⭐ NEW!

## Troubleshooting 🔍

### Issue: "No previous files found"
**Solution:** This is normal for the first stage (Requirements). Later stages should show previous files.

### Issue: Generated files don't match previous stages
**Solution:** 
1. Check `stage_metadata.json` to see what was referenced
2. Regenerate the stage
3. Verify previous stage files exist and have content

### Issue: Want to see all referenced content
**Solution:**
1. Navigate to the stage folder
2. Open `stage_metadata.json`
3. Check the `previous_files_referenced` array
4. Read those files manually if needed

## Example Workflow 📝

### Complete Project Generation

```bash
# 1. Enter project description: "E-commerce shoe store"
# 2. Click "Breakdown Project"
# 3. Build stages in order:

Stage 1: Requirements
- Generates: requirements.md, user_stories.xlsx
- References: None
- Shows: "No previous stages"

Stage 2: Design
- Generates: design_document.md, database_schema.sql, api_contract.yaml
- References: requirements.md, user_stories.xlsx
- Shows: "This stage will build upon: Requirements_GatheringAnd_Analysis"
- Result: Schema matches requirements ✅

Stage 3: Implementation
- Generates: app.py, models.py, routes.py, Dockerfile
- References: All files from Requirements + Design
- Shows: "This stage will build upon: Requirements, Design"
- Result: Code implements designed schema ✅

Stage 4: Testing
- Generates: test_app.py, test_models.py, test_routes.py
- References: All previous files
- Shows: "This stage will build upon: Requirements, Design, Implementation"
- Result: Tests cover actual implementation ✅

Stage 5: Deployment
- Generates: docker-compose.yml, deployment.yaml, nginx.conf
- References: All previous files
- Shows: "This stage will build upon: Requirements, Design, Implementation, Testing"
- Result: Deployment matches implementation needs ✅

Stage 6: Maintenance
- Generates: monitoring.sh, backup.sh, update_procedures.md
- References: All previous files
- Shows: "This stage will build upon: [all previous]"
- Result: Maintenance procedures for actual system ✅

Stage 7: Execution_And_Startup ⭐ NEW!
- Generates: start.sh, start.bat, run.py, README_RUN.md, setup_env.sh
- References: ALL previous files (complete project context)
- Shows: "This stage will build upon: [all 6 previous stages]"
- Result: Project can be started immediately with one command ✅
- Benefit: Zero friction - run ./start.sh and you're done! 🚀
```

## Summary ✨

**Key Improvement:** Each stage now knows about and builds upon previous stages, ensuring your final project is **cohesive, consistent, and working**.

**You Get:**
- ✅ Connected stages with proper context
- ✅ Consistent naming and structures
- ✅ Working final project
- ✅ Full traceability with metadata
- ✅ Better quality generated code

**No Extra Steps Required:** The system handles everything automatically. Just build stages in order and watch the magic happen! 🚀

