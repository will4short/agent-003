"""Lesson 24: per-turn repeated-read reduction, without hiding changed files."""
from pathlib import Path
import hashlib

class ReadContext:
    def __init__(self):
        self.seen = {}

    def read(self, root, filename, reader, allowed):
        if not allowed(root, filename):
            return reader(root, filename)
        path = (Path(root) / filename).resolve()
        if not path.is_file() or path.is_symlink():
            return reader(root, filename)
        try:
            stat = path.stat()
            # Re-hash before suppressing a repeat, to detect same-size edits.
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return reader(root, filename)
        key = str(path)
        if self.seen.get(key) == (stat.st_size, digest):
            return (f"ALREADY_READ_THIS_TURN: {filename}. Content is unchanged and "
                    "was returned earlier in this task turn. Reuse that content; "
                    "do not infer anything not in the earlier tool result.")
        content = reader(root, filename)
        # Cache only successful reads, never error strings.
        if isinstance(content, str) and not content.startswith(("Error:", "Error reading", "Access denied:")):
            self.seen[key] = (stat.st_size, digest)
        return content

    def invalidate(self):
        self.seen.clear()
