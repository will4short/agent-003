"""One-time, fail-closed patch for the Lesson 20 Agent 003 conversation loop."""
from pathlib import Path
import ast
import shutil

path = Path(__file__).resolve().parent / 'agent.py'
src = path.read_text(encoding='utf-8')
if 'LESSON21_COST_GUARD' in src:
    raise SystemExit('Lesson 21 already installed; no changes made.')

# Anchor checks prevent silently patching a different version of the agent.
anchors = [
    'previous_response_id = None\nlast_recovery = None',
    '    response = client.responses.create(**request)',
    '        response = client.responses.create(\n',
    '        print("\\nAgent 003: Goodbye!")',
]
for a in anchors:
    if src.count(a) != 1:
        raise SystemExit(f'Unexpected agent.py structure; stopped without editing: {a!r}')

src = src.replace('previous_response_id = None\nlast_recovery = None',
    '''# LESSON21_COST_GUARD: session-only estimated cost protection.
from agent_cost import CostGuard, BudgetExceeded
try:
    cost_guard = CostGuard.from_environment()
except ValueError as exc:
    raise SystemExit(f"COST CONFIGURATION ERROR: {exc}. See Lesson 21 setup.")

previous_response_id = None
last_recovery = None''', 1)
src = src.replace('    response = client.responses.create(**request)',
    '''    try:
        cost_guard.ensure_can_request()
        response = client.responses.create(**request)
        cost_guard.record(response)
    except BudgetExceeded as exc:
        print(f"\\nCOST LIMIT: {exc}")
        print(cost_guard.summary())
        break
    except Exception as exc:
        print(f"\\nAPI REQUEST FAILED: {type(exc).__name__}: {exc}")
        print(cost_guard.summary())
        break''', 1)
src = src.replace('        response = client.responses.create(\n',
    '''        try:
            cost_guard.ensure_can_request()
            response = client.responses.create(
''', 1)
# Insert closure immediately before the next known loop tail, retaining original call arguments.
tail = '''            tools=tools,
        )

    else:
'''
if src.count(tail) != 1:
    raise SystemExit('Unexpected API continuation structure; stopped without editing.')
src = src.replace(tail, '''            tools=tools,
            )
            cost_guard.record(response)
        except BudgetExceeded as exc:
            print(f"\\nCOST LIMIT: {exc}")
            print(cost_guard.summary())
            previous_response_id = None
            break
        except Exception as exc:
            print(f"\\nAPI REQUEST FAILED: {type(exc).__name__}: {exc}")
            print(cost_guard.summary())
            previous_response_id = None
            break

    else:
''', 1)
src = src.replace('        print("\\nAgent 003: Goodbye!")',
    '        print("\\nAgent 003: Goodbye!")\n        print(cost_guard.summary())', 1)
try:
    ast.parse(src)
except SyntaxError as exc:
    raise SystemExit(f'Generated code invalid; original untouched: {exc}')
backup = path.with_name('agent-before-lesson21-integration.bak')
if backup.exists():
    raise SystemExit(f'Backup already exists: {backup.name}; no changes made.')
shutil.copy2(path, backup)
path.write_text(src, encoding='utf-8')
print('Lesson 21 integration applied. Backup:', backup.name)
