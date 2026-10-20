"""Lesson 29: conservative, read-only tool argument and duplicate-call guard.

Never auto-approves edits, tests or recovery. Only guards analysis tools.
"""
from pathlib import Path
import json

FILE_TOOLS = {'trace_python_calls', 'inspect_python_imports'}
PROJECT_TOOLS = {'trace_local_imports', 'list_files'}
SEARCH_TOOLS = {'find_python_symbols', 'search_code'}
READ_ONLY_TOOLS = FILE_TOOLS | PROJECT_TOOLS | SEARCH_TOOLS | {'read_file'}


def validate_tool_call(name, args):
    """Return (valid, explanation). Fail open for approval-sensitive tools."""
    if name not in READ_ONLY_TOOLS:
        return True, ''
    if not isinstance(args, dict):
        return False, 'Arguments must be a JSON object.'
    if name in FILE_TOOLS | {'read_file'}:
        filename = args.get('filename')
        if not isinstance(filename, str) or not filename.strip():
            return False, f'{name} requires a specific filename.'
        if filename.strip() in {'.', '..', '/', '\\'} or filename.endswith(('/', '\\')):
            return False, f'{name} requires a file, not a directory. Use list_files first.'
        if name in FILE_TOOLS and Path(filename).suffix.lower() != '.py':
            return False, f'{name} requires a .py filename. Use list_files first.'
    if name == 'find_python_symbols' and not str(args.get('query', '')).strip():
        return False, 'Symbol query must not be empty.'
    if name == 'search_code' and not str(args.get('keyword', '')).strip():
        return False, 'Search keyword must not be empty.'
    return True, ''


class ToolCallOptimizer:
    """Deduplicate only successful read-only calls with identical arguments.

    Reuse is scoped to one user task; invalidate after any attempted edit.
    """
    def __init__(self):
        self._cache = {}

    def reset(self):
        self._cache.clear()

    def evaluate(self, name, args):
        valid, reason = validate_tool_call(name, args)
        if not valid:
            return {'status': 'BLOCKED', 'message': reason, 'optimizer': 'invalid_arguments'}
        if name in READ_ONLY_TOOLS:
            key = (name, json.dumps(args, sort_keys=True, default=str))
            if key in self._cache:
                return self._cache[key]
        return None

    def record(self, name, args, result):
        if name not in READ_ONLY_TOOLS or not isinstance(args, dict):
            return
        if isinstance(result, dict):
            if result.get('status') not in {'OK', 'PASS'} or result.get('truncated'):
                return
        elif not isinstance(result, (list, str)):
            return
        key = (name, json.dumps(args, sort_keys=True, default=str))
        self._cache[key] = result


TOOL_EFFICIENCY_GUIDANCE = (
    'Use trace_python_calls with a specific .py filename, never a directory or dot. '
    'Use trace_local_imports for project-wide local dependencies. '
    'Do not repeat a successful read-only tool call with identical arguments. '
    'If a tool is blocked, correct its arguments; do not treat failure as evidence. '
    'Avoid extra symbol/import searches when relationship tools already answer the question. '
    'Once sufficient nontruncated evidence answers the user request, summarize and stop. '
    'These are efficiency guidelines only; never bypass human approval for edits, tests or recovery.'
)
