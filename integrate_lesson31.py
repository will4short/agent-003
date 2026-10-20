"""Install Lesson 31 into agent.py. Run from the Agent 003 repository root."""
from pathlib import Path
import ast
import shutil

root = Path(__file__).resolve().parent
path = root / 'agent.py'
s = path.read_text(encoding='utf-8')
if 'LESSON31_PROJECT_INVESTIGATION' in s:
    raise SystemExit('Lesson 31 already installed; no changes made.')
anchors = [
    'tools.extend(RELATIONSHIP_TOOLS)',
    '                elif tool_call.name == "list_files":',
    '    "For call relationships, prefer trace_python_calls over full file reads. "',
]
for anchor in anchors:
    if s.count(anchor) != 1:
        raise SystemExit(f'Cannot safely install: expected exactly one anchor: {anchor[:65]}')
s = s.replace('tools.extend(RELATIONSHIP_TOOLS)', '''tools.extend(RELATIONSHIP_TOOLS)
# LESSON31_PROJECT_INVESTIGATION: static, bounded navigation only.
from agent_project_investigation import investigate_project
INVESTIGATION_TOOLS = [{
    "type": "function", "name": "investigate_project",
    "description": "Find likely Python files for a coding question by matching filenames and AST symbol names. Read-only static shortlist; not a diagnosis.",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}},
                   "required": ["query"], "additionalProperties": False}, "strict": True,
}]
tools.extend(INVESTIGATION_TOOLS)''', 1)
s = s.replace('                elif tool_call.name == "list_files":', '''                elif tool_call.name == "investigate_project":
                    result = investigate_project(PROJECT_ROOT, arguments["query"], is_safe_project_file)

                elif tool_call.name == "list_files":''', 1)
s = s.replace('    "For call relationships, prefer trace_python_calls over full file reads. "', '''    "For unfamiliar Python bugs, use investigate_project to shortlist relevant files, "
    "then inspect source and related tests before making a diagnosis. "
    "Do not present filename/symbol matches as proof of root cause. "
    "For call relationships, prefer trace_python_calls over full file reads. "''', 1)
ast.parse(s, filename='agent.py')
backup = root / 'agent-before-lesson31-integration.bak'
if backup.exists():
    raise SystemExit('Backup already exists; refusing to overwrite it.')
shutil.copy2(path, backup)
path.write_text(s, encoding='utf-8')
print('Lesson 31 installed. Backup:', backup.name)
