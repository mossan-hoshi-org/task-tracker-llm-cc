# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a task time tracking web application that allows users to switch between different work tasks and record time spent. The application consists of:

- **Backend**: FastAPI (Python 3.12+) with pytest for testing
- **Frontend**: Next.js 15 with TypeScript, shadcn/ui, Tailwind CSS, Zustand for state management
- **Package Management**: `uv` for Python dependencies
- **Development Approach**: Test-Driven Development (TDD)

The application integrates with Google Gemini API to automatically categorize work sessions and generate Markdown summaries.

## Key Architecture

### Backend Structure
- FastAPI REST API with the following main endpoints:
  - `POST /sessions/start` - Start new work session
  - `PATCH /sessions/{id}/pause` - Pause/resume session
  - `POST /sessions/{id}/stop` - Stop session
  - `GET /sessions/active` - Get current active sessions
  - `POST /summary/generate` - Generate categorized summary via Gemini API
  - `GET /summary/markdown` - Get formatted Markdown output

### Frontend Structure
- Next.js 15 with App Router
- Two main pages: Main (timer interface) and Summary (categorized results)
- Real-time session tracking with 1-second updates
- Clipboard API integration for Markdown copying

### Session Management Logic
- Only one active session at a time - starting new session auto-stops previous
- Sessions can be paused/resumed independently
- All sessions are stopped when user requests summary
- Time tracking uses server-side timestamps for accuracy

## Development Commands

### Backend Setup and Commands
```bash
# Initialize Python project with uv
uv init

# Install dependencies
uv sync

# Run development server
uv run fastapi dev

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/test_sessions.py::test_start_session

# Run tests with coverage
uv run pytest --cov

# Type checking (if mypy is added)
uv run mypy .
```

### Frontend Setup and Commands
```bash
# Initialize Next.js project
npx create-next-app@latest --typescript --tailwind --app

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Run specific test
npm test -- SessionForm.test.tsx

# Build for production
npm run build

# Type checking
npm run type-check
```

## TDD Development Workflow

1. **Backend First**: Start with API endpoints, write tests before implementation
2. **Frontend Integration**: Build UI components that consume the tested APIs
3. **Test Execution Order**: 
   - Unit tests for models and services
   - API endpoint tests
   - Frontend component tests
   - Integration tests

## Important Implementation Notes

- Gemini API key must be managed via environment variables (`GEMINI_API_KEY`)
- Session timing uses server-side datetime to handle timezone issues
- Frontend real-time updates should use polling or WebSocket for session status
- CORS must be configured for frontend-backend communication
- Error handling is critical - API failures should not crash the application
- Japanese language input support is required throughout the UI

## Core Business Logic

- Session auto-switching: When user starts new task, previous session stops automatically
- Time calculation: Track start_time, pause_time, resume_time for accurate duration
- Category classification: Send completed sessions to Gemini API for categorization
- Markdown generation: Format categorized results as structured Markdown for copying

## Claude Memories

- ultrathink