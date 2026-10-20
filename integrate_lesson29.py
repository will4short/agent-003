"""Idempotent installer for Agent 003 Lesson 29. Run from agent-003 root."""
from pathlib import Path
import ast
import shutil

root = Path(__file__).resolve().parent
path = root / 'agent.py'
source = path.read_text(encoding='utf-8')
if 'LESSON29_TOOL_OPTIMIZER' in source:
    print('Lesson 29 already installed; no changes made.')
    raise SystemExit(0)

required = [
    '    read_context.invalidate()  # One cache per user task turn.',
    '            try:\n                arguments = json.loads(tool_call.arguments)',
    '            session_recorder.record(tool_call.name, result)',
    '            if tool_call.name in {"propose_edit", "propose_multi_edit", "propose_recovery"}:',
]
for marker in required:
    if marker not in source:
        raise SystemExit(f'Cannot safely install: missing integration anchor: {marker[:80]}')

source = source.replace(
    'read_context = ReadContext()',
    'read_context = ReadContext()\n'
    'from agent_tool_optimizer import ToolCallOptimizer, TOOL_EFFICIENCY_GUIDANCE  # LESSON29_TOOL_OPTIMIZER\n'
    'tool_optimizer = ToolCallOptimizer()\n'
    'instructions += " " + TOOL_EFFICIENCY_GUIDANCE', 1)
source = source.replace(
    '    read_context.invalidate()  # One cache per user task turn.',
    '    read_context.invalidate()  # One cache per user task turn.\n'
    '    tool_optimizer.reset()  # LESSON29: task-scoped read-only cache.', 1)
source = source.replace(
    '            try:\n                arguments = json.loads(tool_call.arguments)',
    '            arguments = None  # LESSON29: prevent stale args after parse failures.\n'
    '            try:\n'
    '                arguments = json.loads(tool_call.arguments)\n'
    '                optimization = tool_optimizer.evaluate(tool_call.name, arguments)\n'
    '                if optimization is not None:\n'
    '                    result = optimization\n'
    '                else:\n'
    '                    result = None\n'
    '                if optimization is None:\n'
    '                    result = _execute_optimized_tool_placeholder\n', 1)
# Avoid indenting the entire existing dispatch by using a dedicated exception caught
# before the original dispatcher; cached results are returned through a narrow exception.
placeholder = ('                if optimization is None:\n'
               '                    result = _execute_optimized_tool_placeholder\n')
source = source.replace(placeholder, '                if optimization is not None:\n                    raise _Lesson29ShortCircuit(optimization)\n', 1)
# Catch short-circuit separately, preserving the existing broad exception handler.
source = source.replace(
    '            except Exception as error:\n                result = f"Tool error: {type(error).__name__}"',
    '            except _Lesson29ShortCircuit as short_circuit:\n'
    '                result = short_circuit.result\n'
    '            except Exception as error:\n'
    '                result = f"Tool error: {type(error).__name__}"', 1)
source = source.replace(
    '            session_recorder.record(tool_call.name, result)',
    '            if isinstance(arguments, dict):\n'
    '                tool_optimizer.record(tool_call.name, arguments, result)\n'
    '            session_recorder.record(tool_call.name, result)', 1)
source = source.replace(
    '                read_context.invalidate()  # Conservative: approval may have changed files.',
    '                read_context.invalidate()  # Conservative: approval may have changed files.\n'
    '                tool_optimizer.reset()  # Do not reuse analysis after edit/recovery.', 1)
source = source.replace(
    'while True:\n\n    print("\\nYou:")',
    'class _Lesson29ShortCircuit(Exception):\n'
    '    def __init__(self, result):\n'
    '        self.result = result\n\n'
    'while True:\n\n    print("\\nYou:")', 1)
# Use syntax verification before any filesystem write.
ast.parse(source, filename='agent.py')
backup = root / 'agent-before-lesson29-integration.bak'
if backup.exists():
    raise SystemExit('Backup already exists; refusing to overwrite it.')
shutil.copy2(path, backup)
path.write_text(source, encoding='utf-8')
print('Lesson 29 installed. Backup:', backup.name)
