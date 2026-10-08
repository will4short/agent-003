# Agent 003 — Project-Aware Coding Agent

A Python-based AI coding assistant built from first principles.

Agent 003 can inspect existing software projects, search source code,
analyze Git changes, and propose code improvements with human approval.

## Features

- Dynamic project selection
- Recursive project file discovery
- Source code searching
- File reading with basic access restrictions
- Conversational AI with session context
- Git status inspection
- Git diff inspection
- AI-generated code change proposals
- Human approval before applying edits
- Basic file-version verification

## Architecture

User Request
    ↓
AI Model
    ↓
Tool Selection
    ↓
Python Tool Execution
    ↓
Tool Results
    ↓
AI Reasoning
    ↓
Final Response

## Available Tools

- list_files
- search_code
- read_file
- get_git_status
- get_git_diff
- propose_edit

## Installation

1. Create a Python virtual environment.
2. Install dependencies:

   pip install openai python-dotenv

3. Create a `.env` file containing:

   OPENAI_API_KEY=your_api_key

## Usage

Run:

    python agent.py "PATH_TO_PROJECT"

Example:

    python agent.py "..\agent-002"

Then enter your instructions.

Type `exit` to end the session.

## Safety

Agent 003 uses basic file-access restrictions and requires explicit
human approval before applying proposed edits.

It is an educational prototype, not a production-safe coding agent.

Use disposable projects for editing experiments.

## Development Status

Version: 0.1

Completed:
- Project discovery
- Code search and reading
- Conversational tool calling
- Git inspection
- Change proposals
- Human-approved editing

Planned:
- Automated verification
- Improved security boundaries
- Better handling of large repositories
- Change review and rollback