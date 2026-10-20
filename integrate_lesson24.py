"""Idempotent, guarded Lesson 24 installer. Run beside agent.py."""
from pathlib import Path
import shutil

p = Path(__file__).resolve().with_name('agent.py')
s = p.read_text(encoding='utf-8')
marker = '# LESSON24_CONTEXT_INTEGRATION'
if marker in s:
    print('Lesson 24 already installed; no changes made.')
    raise SystemExit(0)

replacements = [
    ('previous_response_id = None\nlast_recovery = None',
     'from agent_context import ReadContext  # LESSON24_CONTEXT_INTEGRATION\n'
     'read_context = ReadContext()\n'
     'previous_response_id = None\nlast_recovery = None'),
    ('    user_goal = "\\n".join(message_lines).strip()\n',
     '    user_goal = "\\n".join(message_lines).strip()\n'
     '    read_context.invalidate()  # One cache per user task turn.\n'),
    ('                    result = read_project_file(\n                        PROJECT_ROOT,\n                        arguments["filename"]\n                    )',
     '                    result = read_context.read(\n                        PROJECT_ROOT, arguments["filename"],\n                        read_project_file, is_safe_project_file\n                    )'),
    ('            session_recorder.record(tool_call.name, result)',
     '            if tool_call.name in {"propose_edit", "propose_multi_edit", "propose_recovery"}:\n'
     '                read_context.invalidate()  # Conservative: approval may have changed files.\n'
     '            session_recorder.record(tool_call.name, result)'),
    ('    "For nontrivial multi-step tasks, first use create_task_plan with 2 to 6 concise steps. "',
     '    "For nontrivial multi-step tasks, first use create_task_plan with 2 to 6 concise steps. "\n'
     '    "After planning, immediately continue permitted read-only inspection and verification in the same turn; "\n'
     '    "do not stop merely to restate the plan. Respect tool limits and cost budget. "\n'
     '    "Only mark steps complete after successful relevant tool evidence; reporting is complete when you report. "\n'
     '    "Do not perform edits or test execution without the existing human approval gates. "'),
]
for old, new in replacements:
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'Installer stopped safely: expected exactly one integration anchor; found {count}: {old[:65]!r}')
    s = s.replace(old, new, 1)
backup = p.with_name('agent-before-lesson24-integration.bak')
if backup.exists():
    raise SystemExit(f'Backup already exists: {backup.name}. No changes made.')
shutil.copy2(p, backup)
try:
    p.write_text(s, encoding='utf-8')
except BaseException:
    shutil.copy2(backup, p)
    raise
print('Lesson 24 installed. Backup:', backup.name)
