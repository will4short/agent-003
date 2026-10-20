"""Lesson 28: classify tool evidence without executing code or changing approvals."""

READ_ONLY_TOOLS = frozenset({
    'list_files', 'search_code', 'read_file', 'get_git_status', 'get_git_diff',
    'find_python_symbols', 'inspect_python_imports', 'trace_python_calls',
    'trace_local_imports', 'verify_python', 'diagnose_last_failure',
})
FAILURE_STATES = frozenset({'ERROR', 'FAIL', 'FAILED', 'BLOCKED', 'REJECTED',
                            'CANCELLED', 'TIMEOUT', 'UNAVAILABLE', 'PARTIAL_FAILURE',
                            'ROLLED_BACK', 'REVISION_REQUESTED'})
SUCCESS_STATES = frozenset({'OK', 'PASS', 'APPLIED', 'SUCCESS'})


def validate_tool_result(tool_name, result):
    """Return a bounded advisory evidence assessment; never approve an action."""
    if not isinstance(tool_name, str) or not tool_name:
        return {'quality': 'UNKNOWN', 'guidance': 'Tool identity is missing; do not assert success.'}
    if isinstance(result, str):
        if result.startswith(('Tool error:', 'Error:', 'Access denied:', 'Git error:')):
            return {'quality': 'FAILED', 'guidance': 'Tool reported an error; do not infer requested results.'}
        # Plain text and lists may be valid legacy tool responses, but do not certify completeness.
        return {'quality': 'UNVERIFIED', 'guidance': 'Unstructured tool output; avoid claims of exhaustive coverage.'}
    if isinstance(result, dict):
        status = str(result.get('status', '')).upper()
        if status in FAILURE_STATES:
            return {'quality': 'FAILED', 'guidance': 'Tool did not complete successfully. Explain the limitation; never claim success.'}
        if status and status not in SUCCESS_STATES:
            return {'quality': 'UNVERIFIED', 'guidance': 'Unrecognized status; do not assume success.'}
        if result.get('truncated') is True:
            return {'quality': 'INCOMPLETE', 'guidance': 'Results are truncated. Report partial coverage; do not claim all matches or dependencies were found.'}
        if result.get('truncated') not in (None, False, True):
            return {'quality': 'UNVERIFIED', 'guidance': 'Truncation flag is invalid; completeness is unknown.'}
        if not status:
            return {'quality': 'UNVERIFIED', 'guidance': 'No explicit status; interpret output cautiously.'}
        if tool_name in {'trace_python_calls', 'trace_local_imports', 'find_python_symbols', 'inspect_python_imports'}:
            return {'quality': 'STATIC_ONLY', 'guidance': 'Static analysis only; dynamic calls/imports may not be resolved.'}
        return {'quality': 'SUPPORTED', 'guidance': 'Tool reports success; limit conclusions to evidence returned.'}
    if isinstance(result, list):
        return {'quality': 'UNVERIFIED', 'guidance': 'List results may be bounded; do not claim exhaustive coverage.'}
    return {'quality': 'UNVERIFIED', 'guidance': 'Unknown tool result format; do not assert success.'}


def model_tool_output(tool_name, result):
    """Attach validation to read-only results only; leave approval-gated outputs intact."""
    if tool_name not in READ_ONLY_TOOLS:
        return result
    return {'tool_result': result, 'evidence_validation': validate_tool_result(tool_name, result)}
