"""Lesson 26: bounded static Python call and local-import analysis.

Never imports or executes project source. Results are syntactic, not runtime proofs.
"""
import ast
from pathlib import Path

MAX_BYTES = 100_000
MAX_FILES = 250
MAX_EDGES = 100
SKIP = {'.git', '.venv', 'venv', 'node_modules', '.expo', '.next', 'dist', 'build', '__pycache__'}


def _source(root, filename, safe_file):
    root = Path(root).resolve()
    if not isinstance(filename, str) or not filename or not safe_file(root, filename):
        return None, {'status': 'BLOCKED', 'message': 'Restricted filename.'}
    raw = root / filename
    if raw.is_symlink():
        return None, {'status': 'BLOCKED', 'message': 'Symlinks are not permitted.'}
    path = raw.resolve()
    if path.suffix.lower() != '.py' or not path.is_file():
        return None, {'status': 'BLOCKED', 'message': 'Existing Python file required.'}
    try:
        if path.stat().st_size > MAX_BYTES:
            return None, {'status': 'BLOCKED', 'message': 'File too large.'}
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=filename)
    except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
        return None, {'status': 'ERROR', 'message': type(exc).__name__}
    return tree, None


def _call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f'{base}.{node.attr}' if base else node.attr
    return None


def trace_python_calls(root, filename, safe_file):
    """Show syntactic calls and lexical caller scopes in a single Python file."""
    tree, error = _source(root, filename, safe_file)
    if error:
        return error
    edges = []
    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.scope = []
        def visit_FunctionDef(self, node):
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()
        visit_AsyncFunctionDef = visit_FunctionDef
        def visit_ClassDef(self, node):
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()
        def visit_Call(self, node):
            name = _call_name(node.func)
            if name and len(edges) < MAX_EDGES:
                edges.append({'caller': '.'.join(self.scope) or '<module>', 'callee': name, 'line': node.lineno})
            self.generic_visit(node)
    Visitor().visit(tree)
    return {'status': 'OK', 'file': filename, 'calls': edges, 'truncated': len(edges) >= MAX_EDGES,
            'note': 'Static syntax only; calls may target external objects or dynamic bindings.'}


def trace_local_imports(root, safe_file):
    """Find local module dependencies using AST import declarations."""
    root = Path(root).resolve()
    modules = {}
    scanned = 0
    for path in sorted(root.rglob('*.py')):
        rel = path.relative_to(root)
        if any(part in SKIP for part in rel.parts[:-1]) or path.is_symlink() or not path.is_file():
            continue
        filename = rel.as_posix()
        if not safe_file(root, filename):
            continue
        scanned += 1
        if scanned > MAX_FILES:
            break
        dotted = '.'.join(rel.with_suffix('').parts)
        if dotted.endswith('.__init__'):
            dotted = dotted[:-9]
        if dotted:
            modules[dotted] = filename
    edges = []
    for module, filename in modules.items():
        tree, error = _source(root, filename, safe_file)
        if error:
            continue
        package = module if filename.endswith('/__init__.py') else module.rpartition('.')[0]
        for node in ast.walk(tree):
            candidates = []
            if isinstance(node, ast.Import):
                candidates = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    bits = package.split('.') if package else []
                    keep = len(bits) - (node.level - 1)
                    if keep < 0:
                        continue
                    base = '.'.join(bits[:keep] + ([node.module] if node.module else []))
                else:
                    base = node.module or ''
                candidates = [base] + [f'{base}.{a.name}' if base else a.name for a in node.names]
            for candidate in candidates:
                # Only report known local Python modules; no imports are executed.
                target = candidate
                while target and target not in modules:
                    target = target.rpartition('.')[0]
                if target and modules[target] != filename:
                    edge = {'source': filename, 'target': modules[target], 'line': node.lineno}
                    if edge not in edges:
                        edges.append(edge)
                    if len(edges) >= MAX_EDGES:
                        return {'status': 'OK', 'dependencies': edges, 'files_inspected': min(scanned, MAX_FILES), 'truncated': True}
    return {'status': 'OK', 'dependencies': edges, 'files_inspected': min(scanned, MAX_FILES), 'truncated': scanned > MAX_FILES}
