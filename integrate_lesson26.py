"""Install Lesson 26 into agent.py. Idempotent; refuses unexpected layouts."""
from pathlib import Path
import ast
import shutil

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'agent.py'
MARKER = '# LESSON26_RELATIONSHIPS'


def integrate():
    if not (ROOT / 'agent_relationships.py').is_file():
        raise SystemExit('Missing agent_relationships.py in this folder.')
    source = TARGET.read_text(encoding='utf-8')
    if MARKER in source:
        print('Lesson 26 already installed; no changes made.')
        return
    registration = 'tools.extend(SYMBOL_TOOLS)  # LESSON25_TOOL_REGISTRATION'
    dispatch = '                elif tool_call.name == "list_files":'
    prompt = '    "Prefer find_python_symbols for locating Python definitions'
    for needle in (registration, dispatch, prompt):
        if source.count(needle) != 1:
            raise SystemExit(f'Unexpected agent.py layout; installation stopped at: {needle[:65]}')
    source = source.replace(registration, registration + '''
# LESSON26_RELATIONSHIPS
from agent_relationships import trace_python_calls, trace_local_imports
RELATIONSHIP_TOOLS = [
    {"type": "function", "name": "trace_python_calls",
     "description": "Trace syntactic function calls in a Python file; use FIRST for who-calls-whom questions. Static analysis only.",
     "parameters": {"type": "object", "properties": {"filename": {"type": "string"}},
                    "required": ["filename"], "additionalProperties": False}, "strict": True},
    {"type": "function", "name": "trace_local_imports",
     "description": "Trace dependencies between local Python modules across the project; use FIRST for local-module relationship questions.",
     "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}, "strict": True},
]
tools.extend(RELATIONSHIP_TOOLS)
''')
    source = source.replace(dispatch, '''                elif tool_call.name == "trace_python_calls":
                    result = trace_python_calls(PROJECT_ROOT, arguments["filename"], is_safe_project_file)

                elif tool_call.name == "trace_local_imports":
                    result = trace_local_imports(PROJECT_ROOT, is_safe_project_file)

''' + dispatch)
    source = source.replace(prompt, '''    "For call relationships, prefer trace_python_calls over full file reads. "
    "For relationships among local Python modules, prefer trace_local_imports. "
    "These tools are static approximations, not runtime call proofs. "
''' + prompt)
    ast.parse(source)
    backup = ROOT / 'agent-before-lesson26-integration.bak'
    if backup.exists():
        raise SystemExit('Backup path already exists; refusing to overwrite.')
    shutil.copy2(TARGET, backup)
    TARGET.write_text(source, encoding='utf-8')
    print('Lesson 26 installed. Backup:', backup.name)


if __name__ == '__main__':
    integrate()
