"""Lesson 31: bounded, read-only Python project investigation. Never executes source."""
import ast
from pathlib import Path

SKIP = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'dist', 'build', '.next', '.expo'}
MAX_FILES = 150
MAX_BYTES = 100_000
MAX_RESULTS = 12


def investigate_project(root, query, allowed):
    """Find likely Python files and static relationships for a task description."""
    if not isinstance(query, str) or not query.strip():
        return {'status': 'BLOCKED', 'message': 'A nonempty investigation query is required.'}
    root = Path(root).resolve()
    tokens = {word.lower() for word in __import__('re').findall(r'[A-Za-z_][A-Za-z_0-9]*', query)
              if len(word) >= 3 and word.lower() not in {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'file', 'code', 'python', 'function', 'project', 'investigate', 'find', 'issue', 'bug'}}
    files = []
    skipped = 0
    for path in sorted(root.rglob('*.py')):
        rel = path.relative_to(root)
        if any(part in SKIP for part in rel.parts[:-1]) or path.is_symlink() or not path.is_file() or not allowed(root, rel.as_posix()):
            continue
        if len(files) >= MAX_FILES:
            skipped += 1
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                skipped += 1
                continue
            source = path.read_text(encoding='utf-8')
            tree = ast.parse(source, filename=rel.as_posix())
        except (OSError, UnicodeError, SyntaxError, ValueError):
            skipped += 1
            continue
        symbols = []
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.append({'name': node.name, 'line': node.lineno})
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append('.' * node.level + node.module)
        haystack = rel.as_posix().lower() + ' ' + ' '.join(x['name'].lower() for x in symbols)
        matches = sorted(t for t in tokens if t in haystack)
        score = sum(3 if t in rel.as_posix().lower() else 1 for t in matches)
        files.append({'file': rel.as_posix(), 'score': score, 'matched_terms': matches,
                      'symbols': symbols[:20], 'imports': imports[:20]})
    files.sort(key=lambda x: (-x['score'], x['file']))
    relevant = [x for x in files if x['score'] > 0][:MAX_RESULTS]
    # No textual or runtime proof of a bug: this is only a navigation shortlist.
    return {'status': 'OK', 'query': query[:200], 'files_inspected': len(files),
            'candidates': relevant, 'truncated': skipped > 0 or len([x for x in files if x['score'] > 0]) > MAX_RESULTS,
            'limitations': 'Static filename/symbol matching only; inspect source and tests before diagnosing causes.'}
