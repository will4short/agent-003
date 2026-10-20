"""Lesson 30: fail-closed, content-aware caching for read-only project tools.

Never caches edits, tests, recovery, failed results, or incomplete scans.
"""
from pathlib import Path
import hashlib
import json

from agent_tool_optimizer import ToolCallOptimizer, READ_ONLY_TOOLS

MAX_FILES = 250
MAX_BYTES = 100_000
IGNORED = {'.git', '.venv', 'venv', 'node_modules', '.expo', '.next', 'dist', 'build', '__pycache__'}


class FileAwareToolCallOptimizer(ToolCallOptimizer):
    """Reuse successful analysis only while the relevant source snapshot matches."""

    def __init__(self, project_root):
        super().__init__()
        self.root = Path(project_root).resolve()
        self._snapshots = {}

    def reset(self):
        super().reset()
        self._snapshots.clear()

    def _file_digest(self, filename):
        if not isinstance(filename, str):
            return None
        raw = self.root / filename
        if raw.is_symlink():
            return None
        path = raw.resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            return None
        relative = path.relative_to(self.root)
        if any(part in IGNORED for part in relative.parts[:-1]):
            return None
        try:
            if path.stat().st_size > MAX_BYTES:
                return None
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return None

    def _snapshot(self, name, args):
        if name not in READ_ONLY_TOOLS or name == 'read_file':
            return None  # ReadContext already handles repeat reads and content changes.
        if name in {'trace_python_calls', 'inspect_python_imports'}:
            filename = args.get('filename')
            digest = self._file_digest(filename)
            return ('file', filename, digest) if digest is not None else None
        # Search, module graph, and listings depend on the entire project.
        # Fail closed if a bounded snapshot cannot cover every eligible source.
        rows = []
        try:
            for path in sorted(self.root.rglob('*')):
                rel = path.relative_to(self.root)
                if any(part in IGNORED for part in rel.parts[:-1]):
                    continue
                if path.is_symlink() or not path.is_file():
                    continue
                if path.suffix.lower() not in {'.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.txt', '.css', '.html', '.yaml', '.yml'}:
                    continue
                if len(rows) >= MAX_FILES or path.stat().st_size > MAX_BYTES:
                    return None
                digest = self._file_digest(rel.as_posix())
                if digest is None:
                    return None
                rows.append((rel.as_posix(), digest))
        except OSError:
            return None
        return ('project', tuple(rows))

    @staticmethod
    def _key(name, args):
        return (name, json.dumps(args, sort_keys=True, default=str))

    def evaluate(self, name, args):
        # Base class handles invalid arguments. Never reuse its cache directly.
        from agent_tool_optimizer import validate_tool_call
        valid, reason = validate_tool_call(name, args)
        if not valid:
            return {'status': 'BLOCKED', 'message': reason, 'optimizer': 'invalid_arguments'}
        if name not in READ_ONLY_TOOLS or not isinstance(args, dict):
            return None
        key = self._key(name, args)
        cached = self._cache.get(key)
        if cached is None:
            return None
        snapshot = self._snapshot(name, args)
        if snapshot is not None and snapshot == self._snapshots.get(key):
            return cached
        self._cache.pop(key, None)
        self._snapshots.pop(key, None)
        return None

    def record(self, name, args, result):
        if name not in READ_ONLY_TOOLS or name == 'read_file' or not isinstance(args, dict):
            return
        if not isinstance(result, dict) or result.get('status') not in {'OK', 'PASS'}:
            return
        if result.get('truncated') is not False:
            return  # Require explicit evidence of completeness.
        snapshot = self._snapshot(name, args)
        if snapshot is None:
            return
        key = self._key(name, args)
        self._cache[key] = result
        self._snapshots[key] = snapshot
