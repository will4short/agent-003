"""One-time, conservative Lesson 20 integration for a clean Lesson 19 agent.py.

Run from the agent-003 directory. Refuses unexpected code layouts.
"""
from pathlib import Path
import ast
import sys

path = Path('agent.py')
if not path.is_file():
    sys.exit('ERROR: Run from the agent-003 directory containing agent.py.')
original = path.read_text(encoding='utf-8')
if 'LESSON20_SESSION_INTEGRATION' in original:
    sys.exit('Already integrated; no changes made.')

replacements = [
    ('previous_response_id = None\nlast_recovery = None  # In-memory; lasts only for this process.\n',
     'from agent_session_runtime import SessionRecorder  # LESSON20_SESSION_INTEGRATION\n'
     'session_recorder = SessionRecorder()\n'
     'print("\\nMEMORY STATUS:", session_recorder.startup_message())\n'
     'instructions += " " + session_recorder.context_for_model()\n'
     'previous_response_id = None\nlast_recovery = None  # In-memory; lasts only for this process.\n'),
    ('        print("\\nAgent 003: Goodbye!")\n        break\n',
     '        session_recorder.finish()\n'
     '        print("\\nAgent 003: Goodbye!")\n        break\n'),
    ('            print(f"Tool result: {str(result)[:1000]}")\n',
     '            session_recorder.record(tool_call.name, result)\n'
     '            print(f"Tool result: {str(result)[:1000]}")\n'),
]
updated = original
for old, new in replacements:
    count = updated.count(old)
    if count != 1:
        sys.exit(f'ERROR: Expected exactly one integration anchor, found {count}: {old[:65]!r}. No changes made.')
    updated = updated.replace(old, new, 1)
try:
    ast.parse(updated, filename='agent.py')
except SyntaxError as exc:
    sys.exit(f'ERROR: Integrated code fails syntax check: {exc}. No changes made.')
# Backup is separate from the user's existing lesson20 backup.
backup = Path('agent-before-lesson20-integration.bak')
if backup.exists():
    sys.exit('ERROR: Integration backup already exists. No changes made.')
backup.write_text(original, encoding='utf-8')
path.write_text(updated, encoding='utf-8')
print('Lesson 20 integration applied. Original saved as', backup)
print('Next: run syntax checks, memory tests, and Lesson 19 regression tests.')
