# EduLink v0.2.0 Release Notes

**Release Date:** 2026-03-22

## Overview
This release focuses on deployment stability, advanced feature testing, and release preparation.

## Key Features
- ??Unified execution entrypoint (app_jwt.py)
- ??Complete API documentation (50+ endpoints)
- ??Full user journey integration tests
- ??RBAC implementation (student/instructor/admin)
- ??Health check & metrics endpoints
- ??Docker & Docker Compose support

## Improvements
- Enhanced test coverage with journey-based scenarios
- Improved response consistency across endpoints
- Better error handling and status codes
- Environment variable support for flexible configuration

## Recent Changes
- fatal: ambiguous argument 'v0.1.0..HEAD': unknown revision or path not in the working tree.
- Use '--' to separate paths from revisions, like this:
- 'git <command> [<revision>...] -- [<file>...]'

## Testing
- Backend Tests: 30+ passing (pytest)
- Integration: Full user journey covered
- API Validation: All 50+ endpoints tested
- Health Check: Endpoint verified

## Known Issues
- None

## Next Steps (v0.3.0)
- Advanced tax workflow integration
- Network feature expansion
- Admin dashboard analytics
- Performance optimization

## Installation
\\\ash
# Local development
python run.py

# Docker
docker-compose -f docker/docker-compose.yml up -d

# Tests
pytest tests/ -v
\\\

## Contributors
- EduLink Development Team

---
**For detailed API documentation, see [API_SPEC.md](./API_SPEC.md)**
