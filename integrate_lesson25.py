"""Guarded, idempotent Lesson 25 integration. Run beside agent.py."""
from pathlib import Path
import shutil

p = Path(__file__).resolve().with_name('agent.py')
s = p.read_text(encoding='utf-8')
marker = '# LESSON25_SYMBOL_SEARCH'
if marker in s:
    print('Lesson 25 already installed; no changes made.')
    raise SystemExit(0)

replacements = [
    ('tools = [\n', '''from agent_symbols import search_python_symbols, python_module_imports  # LESSON25_SYMBOL_SEARCH

SYMBOL_TOOLS = [
    {
        "type": "function", "name": "find_python_symbols",
        "description": "Find Python function, async function, method, or class definitions by name without reading whole files or executing code.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}},
                       "required": ["query"], "additionalProperties": False}, "strict": True,
    },
    {
        "type": "function", "name": "inspect_python_imports",
        "description": "List imports declared in one Python file without importing or executing it.",
        "parameters": {"type": "object", "properties": {"filename": {"type": "string"}},
                       "required": ["filename"], "additionalProperties": False}, "strict": True,
    },
]

tools = [
'''),
    ('                elif tool_call.name == "list_files":', '''                elif tool_call.name == "find_python_symbols":
                    result = search_python_symbols(PROJECT_ROOT, arguments["query"], is_safe_project_file)

                elif tool_call.name == "inspect_python_imports":
                    result = python_module_imports(PROJECT_ROOT, arguments["filename"], is_safe_project_file)

                elif tool_call.name == "list_files":'''),
    ('    "For nontrivial multi-step tasks, first use create_task_plan with 2 to 6 concise steps. "', '''    "Prefer find_python_symbols for locating Python definitions and inspect_python_imports for dependency discovery; "
    "use read_file only when source content is necessary. Search results are bounded and do not execute code. "
    "For nontrivial multi-step tasks, first use create_task_plan with 2 to 6 concise steps. "'''),
]
for old, new in replacements:
    if s.count(old) != 1:
        raise SystemExit(f'Installer stopped safely: expected one anchor, got {s.count(old)}: {old[:70]!r}')
    s = s.replace(old, new, 1)
# Locate the tool extension anchor used by earlier lessons, fail closed if absent.
for anchor in ('tools.extend(PLAN_TOOL_DEFINITIONS)', 'tools += PLAN_TOOL_DEFINITIONS', 'tools.extend(PLAN_TOOL_DEFINITIONS)  #'):
    if anchor in s:
        s = s.replace(anchor, anchor + '\ntools.extend(SYMBOL_TOOLS)  # LESSON25_TOOL_REGISTRATION', 1)
        break
else:
    raise SystemExit('Installer stopped safely: plan tool registration anchor missing.')
backup = p.with_name('agent-before-lesson25-integration.bak')
if backup.exists():
    raise SystemExit('Backup already exists; no changes made.')
shutil.copy2(p, backup)
try:
    p.write_text(s, encoding='utf-8')
except BaseException:
    shutil.copy2(backup, p)
    raise
print('Lesson 25 installed. Backup:', backup.name)
