"""Offline tests for Lesson 26 (no OpenAI requests)."""
import tempfile
import unittest
from pathlib import Path
from agent_relationships import trace_python_calls, trace_local_imports


def safe(root, filename):
    root = Path(root).resolve()
    p = (root / filename).resolve()
    return p.is_relative_to(root) and p.suffix == '.py'


class RelationshipsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, content):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')

    def test_call_edges(self):
        self.write('a.py', 'def a():\n    b()\ndef b():\n    pass\na()\n')
        calls = trace_python_calls(self.root, 'a.py', safe)['calls']
        self.assertIn({'caller': 'a', 'callee': 'b', 'line': 2}, calls)
        self.assertIn({'caller': '<module>', 'callee': 'a', 'line': 5}, calls)

    def test_methods(self):
        self.write('a.py', 'class C:\n    def f(self):\n        self.g()\n')
        self.assertEqual(trace_python_calls(self.root, 'a.py', safe)['calls'][0]['caller'], 'C.f')

    def test_local_import(self):
        self.write('a.py', 'from b import run\n')
        self.write('b.py', 'def run(): pass\n')
        deps = trace_local_imports(self.root, safe)['dependencies']
        self.assertTrue(any(e['source'] == 'a.py' and e['target'] == 'b.py' for e in deps))

    def test_relative_import(self):
        self.write('pkg/__init__.py', '')
        self.write('pkg/a.py', 'from . import b\n')
        self.write('pkg/b.py', 'pass\n')
        deps = trace_local_imports(self.root, safe)['dependencies']
        self.assertTrue(any(e['source'] == 'pkg/a.py' and e['target'] == 'pkg/b.py' for e in deps))

    def test_outside_blocked(self):
        self.assertEqual(trace_python_calls(self.root, '../outside.py', safe)['status'], 'BLOCKED')

    def test_missing_blocked(self):
        self.assertEqual(trace_python_calls(self.root, 'missing.py', safe)['status'], 'BLOCKED')

    def test_syntax_error(self):
        self.write('a.py', 'def bad(:\n')
        self.assertEqual(trace_python_calls(self.root, 'a.py', safe)['status'], 'ERROR')

    def test_never_executes(self):
        self.write('a.py', 'raise RuntimeError("do not run")\nprint("hello")\n')
        self.assertEqual(trace_python_calls(self.root, 'a.py', safe)['status'], 'OK')


if __name__ == '__main__':
    unittest.main()
