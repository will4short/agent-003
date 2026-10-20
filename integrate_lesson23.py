"""Install Lesson 23 into Lesson 22 agent.py with guarded, one-time substitutions."""
from pathlib import Path

root = Path(__file__).resolve().parent
agent = root / 'agent.py'
backup = root / 'agent-before-lesson23-integration.bak'
source = agent.read_text(encoding='utf-8')
marker = '# LESSON23_DIAGNOSTICS'
if marker in source:
    print('Lesson 23 already installed; no changes made.')
    raise SystemExit(0)
if 'from agent_planning import TaskPlanner' not in source:
    raise SystemExit('Lesson 22 not found. No changes made.')

changes = [
    ('previous_response_id = None\nlast_recovery = None',
     'from agent_diagnostics import diagnose_failure  ' + marker + '\nlast_failure = None  # Read-only, in-process diagnostic context.\n\nprevious_response_id = None\nlast_recovery = None'),
    ('    "For nontrivial multi-step tasks, first use create_task_plan',
     '    "When verify_python or run_tests fails, use diagnose_last_failure to obtain "\n'
     '    "read-only diagnostic suggestions. Inspect the source before proposing edits. "\n'
     '    "Never treat a diagnosis as proof or permission to modify files. "\n'
     '    "For nontrivial multi-step tasks, first use create_task_plan'),
    ('                if tool_call.name == "create_task_plan":',
     '                if tool_call.name == "diagnose_last_failure":\n'
     '                    result = (diagnose_failure(*last_failure) if last_failure else\n'
     '                              {"status": "UNAVAILABLE", "message": "No recorded failed test or verification."})\n\n'
     '                elif tool_call.name == "create_task_plan":'),
    ('            session_recorder.record(tool_call.name, result)',
     '            if tool_call.name in {"verify_python", "run_tests"} and isinstance(result, dict):\n'
     '                if result.get("status") == "FAIL":\n'
     '                    last_failure = (tool_call.name, result)\n'
     '                elif result.get("status") == "PASS":\n'
     '                    last_failure = None\n'
     '            session_recorder.record(tool_call.name, result)'),
]
for old, new in changes:
    if source.count(old) != 1:
        raise SystemExit(f'Expected exactly one insertion point: {old[:65]!r}. No changes made.')
    source = source.replace(old, new, 1)

# Insert tool declaration before the existing first tool, preserving the list structure.
anchor = 'tools = [\n'
if source.count(anchor) != 1:
    raise SystemExit('Could not locate tools list; no changes made.')
new_tool = '''tools = [
    {
        "type": "function",
        "name": "diagnose_last_failure",
        "description": "Analyze the latest failed Python verification or approved test run; suggestions only, no edits or execution.",
        "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
        "strict": True,
    },
'''
source = source.replace(anchor, new_tool, 1)
compile(source, str(agent), 'exec')
if backup.exists():
    raise SystemExit(f'Backup already exists: {backup.name}. No changes made.')
backup.write_text(agent.read_text(encoding='utf-8'), encoding='utf-8')
try:
    agent.write_text(source, encoding='utf-8')
except Exception:
    agent.write_text(backup.read_text(encoding='utf-8'), encoding='utf-8')
    raise
print('Lesson 23 installed. Backup:', backup.name)
