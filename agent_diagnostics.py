"""Lesson 23: bounded, read-only diagnosis of failed verification/test results."""
import re

MAX_OUTPUT = 4000


def diagnose_failure(tool_name, result):
    """Return cautious suggestions; never execute code or change project files."""
    if tool_name not in {'verify_python', 'run_tests'}:
        return {'status': 'UNAVAILABLE', 'message': 'Only verification and test failures can be diagnosed.'}
    if not isinstance(result, dict) or result.get('status') != 'FAIL':
        return {'status': 'UNAVAILABLE', 'message': 'No failed verification or test result supplied.'}
    raw = result.get('output', result.get('message', ''))
    if not isinstance(raw, str):
        raw = ''
    excerpt = raw[-MAX_OUTPUT:]
    patterns = [
        (r'\bSyntaxError\b|\bIndentationError\b|\bTabError\b', 'Python syntax or indentation error', 'Inspect the indicated file and line; verify indentation, delimiters, and syntax.'),
        (r'\bModuleNotFoundError\b|\bImportError\b', 'Import or dependency problem', 'Check the import name, environment, and available dependencies.'),
        (r'\bAssertionError\b|\bFAIL:\s+test_', 'Test assertion failure', 'Compare expected and actual behavior in the failing test and implementation.'),
        (r'\bNameError\b', 'Undefined name', 'Check variable/function spelling and scope.'),
        (r'\bTypeError\b', 'Type or call mismatch', 'Inspect argument types, function signatures, and return values.'),
        (r'\bAttributeError\b', 'Missing attribute', 'Check the object type and attribute name.'),
        (r'\bFileNotFoundError\b', 'Missing file', 'Check paths and whether the required file exists.'),
        (r'\bPermissionError\b', 'File permission problem', 'Inspect permissions and whether another process holds the file.'),
    ]
    findings = [{'possible_cause': cause, 'suggestion': hint}
                for pattern, cause, hint in patterns if re.search(pattern, excerpt, re.I)][:3]
    if not findings:
        findings = [{'possible_cause': 'Unclassified failure',
                     'suggestion': 'Review the failing output and inspect the related code before proposing changes.'}]
    # Extract bounded location hints, without copying arbitrary failure text or secrets.
    locations = []
    for match in re.finditer(r'File ["\']([^"\'\r\n]{1,160})["\'], line (\d{1,7})', excerpt):
        path = match.group(1)
        if any(part in path.lower() for part in ('.env', 'secret', 'token', 'credential')):
            continue
        locations.append({'file': path.split('/')[-1].split('\\')[-1], 'line': int(match.group(2))})
        if len(locations) == 3:
            break
    return {'status': 'DIAGNOSIS', 'source': tool_name, 'findings': findings,
            'locations': locations,
            'message': 'Heuristic suggestions only. No edits, tests, or rollback performed. Inspect code and request approval before changes.'}
