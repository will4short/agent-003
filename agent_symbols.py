"""Bounded, read-only Python symbol search using the standard-library AST."""
import ast
from pathlib import Path

MAX_FILES = 250
MAX_BYTES = 100_000
MAX_RESULTS = 30


def _source_files(root, safe_file):
    root = Path(root).resolve()
    count = 0
    for path in sorted(root.rglob('*.py')):
        relative = path.relative_to(root).as_posix()
        if any(part in {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'dist', 'build'} for part in path.relative_to(root).parts[:-1]):
            continue
        if path.is_symlink() or not path.is_file() or not safe_file(root, relative):
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
        except OSError:
            continue
        yield path, relative
        count += 1
        if count >= MAX_FILES:
            break


def search_python_symbols(root, query, safe_file):
    """Find Python definitions matching a name substring; never import/execute source."""
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 100:
        return {'status': 'BLOCKED', 'message': 'Query must be 1–100 characters.'}
    needle = query.casefold().strip()
    results = []
    inspected = 0
    for path, relative in _source_files(root, safe_file):
        inspected += 1
        try:
            source = path.read_text(encoding='utf-8')
            tree = ast.parse(source, filename=relative)
        except (OSError, UnicodeError, SyntaxError, ValueError):
            continue
        def walk(body, parent=''):
            for node in body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = f'{parent}.{node.name}' if parent else node.name
                    if needle in name.casefold() and len(results) < MAX_RESULTS:
                        kind = 'class' if isinstance(node, ast.ClassDef) else ('async function' if isinstance(node, ast.AsyncFunctionDef) else 'function')
                        results.append({'file': relative, 'line': node.lineno, 'name': name, 'kind': kind})
                    if isinstance(node, ast.ClassDef):
                        walk(node.body, name)
        walk(tree.body)
        if len(results) >= MAX_RESULTS:
            break
    return {'status': 'OK', 'matches': results, 'files_inspected': inspected, 'truncated': len(results) >= MAX_RESULTS}


def python_module_imports(root, filename, safe_file):
    """List import declarations without importing any modules."""
    root = Path(root).resolve()
    if not isinstance(filename, str) or not safe_file(root, filename):
        return {'status': 'BLOCKED', 'message': 'Restricted file.'}
    raw_path = root / filename
    if raw_path.is_symlink():
        return {'status': 'BLOCKED', 'message': 'Symlinks are not permitted.'}
    path = raw_path.resolve()
    if path.suffix != '.py' or not path.is_file():
        return {'status': 'BLOCKED', 'message': 'Existing non-symlink Python file required.'}
    try:
        if path.stat().st_size > MAX_BYTES:
            return {'status': 'BLOCKED', 'message': 'File too large.'}
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
        return {'status': 'ERROR', 'message': type(exc).__name__}
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({'line': node.lineno, 'module': alias.name, 'relative_level': 0})
        elif isinstance(node, ast.ImportFrom):
            imports.append({'line': node.lineno, 'module': node.module or '', 'relative_level': node.level})
        if len(imports) >= MAX_RESULTS:
            break
    return {'status': 'OK', 'file': filename, 'imports': sorted(imports, key=lambda x: x['line']), 'truncated': len(imports) >= MAX_RESULTS}
