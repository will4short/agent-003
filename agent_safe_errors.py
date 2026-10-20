"""Safe, bounded tool error reports; never expose exception messages or tracebacks."""

KNOWN = {
    'KeyError': 'A required tool argument was missing.',
    'TypeError': 'The tool received arguments of an unexpected type.',
    'ValueError': 'A tool argument or value was invalid.',
    'FileNotFoundError': 'A required file was not found.',
    'PermissionError': 'File access was denied.',
    'UnicodeError': 'The file could not be decoded.',
    'TimeoutExpired': 'The operation timed out.',
}


def safe_tool_error(tool_name, error):
    """Return structured diagnostics without leaking paths, secrets, or raw errors."""
    name = type(error).__name__
    return {
        'status': 'ERROR',
        'tool': tool_name if isinstance(tool_name, str) and tool_name.isidentifier() else 'unknown',
        'error_type': name if name in KNOWN else 'UnexpectedError',
        'message': KNOWN.get(name, 'The tool failed. Check local logs and tool inputs.'),
        'retry_safe': False,
    }
