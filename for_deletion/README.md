# Files Moved to for_deletion

This folder contains files that are not necessary for the core elevator AI agent functionality. These files were moved here for potential cleanup.

## Files Moved:

### Test Files
- `debug_validation.py` - Debug script for timezone validation
- `test_*.py` - Various test scripts for uptime analysis, validation, etc.
- `test_app.sh` - Shell script for testing the application

### Documentation Files
- `COMPREHENSIVE_UPTIME_ANALYSIS_ENHANCEMENT.md` - Documentation about uptime analysis enhancements
- `ENHANCED_UPTIME_ANALYSIS.md` - Documentation about enhanced uptime analysis
- `IMPLEMENTATION_SUMMARY.md` - Implementation summary documentation

### Build/Cache Directories
- `__pycache__/` - Python cache directory from root
- `venv/` - Old virtual environment from root
- `elevator_agent_venv/` - Virtual environment from elevator_ai_agent directory
- `logs/` - Log files from root
- `elevator_agent_logs/` - Log files from elevator_ai_agent directory

## Safe to Delete
All files in this folder are safe to delete as they are:
- Test files that can be regenerated if needed
- Documentation that is not part of the core application
- Cache and build artifacts
- Old virtual environments

## Core Application
The core elevator AI agent functionality remains in the `elevator_ai_agent/` directory with only essential files:
- Application code (`app.py`, etc.)
- Core modules (`agents/`, `services/`, `tools/`, etc.)
- Configuration files (`.env`, `requirements.txt`, etc.)
- Web interface (`static/`, `templates/`)
- README and essential documentation
