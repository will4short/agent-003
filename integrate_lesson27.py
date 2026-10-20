"""Install Lesson 27 tool-routing hints into Agent 003. No API calls."""
import ast
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'agent.py'
MARKER = '# LESSON27_TOOL_ROUTING'


def integrate():
    if not (ROOT / 'agent_tool_selection.py').is_file():
        raise SystemExit('Missing agent_tool_selection.py.')
    original = TARGET.read_text(encoding='utf-8')
    if MARKER in original:
        print('Lesson 27 already installed; no changes made.')
        return
    if 'tools.extend(RELATIONSHIP_TOOLS)' not in original:
        raise SystemExit('Lesson 26 is required. Install it first.')
    needle = '    request = {\n        "model": "gpt-5.5",\n        "instructions": instructions,'
    if original.count(needle) != 1:
        raise SystemExit('Unexpected request layout; no changes made.')
    next_needle = '            instructions=instructions,'
    if original.count(next_needle) != 1:
        raise SystemExit('Unexpected follow-up request layout; no changes made.')
    updated = original.replace(needle, '''    # LESSON27_TOOL_ROUTING: task-specific advice, not permission to execute.
    from agent_tool_selection import tool_guidance
    active_instructions = instructions + tool_guidance(user_goal)

    request = {
        "model": "gpt-5.5",
        "instructions": active_instructions,''')
    updated = updated.replace(next_needle, '            instructions=active_instructions,')
    ast.parse(updated)
    backup = ROOT / 'agent-before-lesson27-integration.bak'
    if backup.exists():
        raise SystemExit('Backup already exists; refusing to overwrite.')
    shutil.copy2(TARGET, backup)
    TARGET.write_text(updated, encoding='utf-8')
    print('Lesson 27 installed. Backup:', backup.name)


if __name__ == '__main__':
    integrate()
