"""Lesson 19: isolated failure-injection tests; never imports agent.py as an app."""
import ast
import difflib
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('agent.py')
FUNCTIONS = {'file_hash', 'is_safe_project_file', 'propose_multi_edit', '_stage_replacement', 'apply_approved_multi_edit'}


def load_functions():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'), filename=str(SOURCE))
    selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FUNCTIONS]
    found = {node.name for node in selected}
    if found != FUNCTIONS:
        raise RuntimeError(f'Missing required functions: {sorted(FUNCTIONS - found)}')
    namespace = {'os': os, 'Path': Path, 'tempfile': tempfile, 'difflib': difflib,
                 'hashlib': hashlib,
                 'MULTI_EDIT_LIMIT': 5,
                 'IGNORED_DIRECTORIES': {'.git', '.venv', 'venv', 'node_modules', '.expo', '.next', 'dist', 'build', '__pycache__'},
                 'ALLOWED_EXTENSIONS': {'.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.txt', '.css', '.html', '.yaml', '.yml'}}
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    exec(compile(module, str(SOURCE), 'exec'), namespace)
    return namespace


class Lesson19FailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = load_functions()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a = self.root / 'first.py'
        self.b = self.root / 'second.py'
        self.a.write_text('value = 1\n', encoding='utf-8')
        self.b.write_text('value = 2\n', encoding='utf-8')
        self.proposal = self.api['propose_multi_edit'](self.root, [
            {'filename': 'first.py', 'new_content': 'value = 10\n'},
            {'filename': 'second.py', 'new_content': 'value = 20\n'},
        ])
        self.assertEqual(self.proposal['status'], 'PENDING', self.proposal)

    def test_second_write_failure_rolls_back_first(self):
        real_replace = os.replace
        count = 0
        def fail_second(src, dst):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError('simulated second write failure')
            return real_replace(src, dst)
        with patch.object(self.api['os'], 'replace', side_effect=fail_second):
            result = self.api['apply_approved_multi_edit'](self.root, self.proposal)
        self.assertEqual(result['status'], 'ROLLED_BACK', result)
        self.assertEqual(result['unresolved'], [])
        self.assertEqual(self.a.read_text(encoding='utf-8'), 'value = 1\n')
        self.assertEqual(self.b.read_text(encoding='utf-8'), 'value = 2\n')
        print('Second write fails -> rollback succeeds:', result)

    def test_rollback_failure_is_reported(self):
        real_replace = os.replace
        count = 0
        def fail_second_and_rollback(src, dst):
            nonlocal count
            count += 1
            if count in (2, 3):
                raise OSError('simulated write/rollback failure')
            return real_replace(src, dst)
        with patch.object(self.api['os'], 'replace', side_effect=fail_second_and_rollback):
            result = self.api['apply_approved_multi_edit'](self.root, self.proposal)
        self.assertEqual(result['status'], 'PARTIAL_FAILURE', result)
        self.assertIn('first.py', result['unresolved'])
        self.assertEqual(self.a.read_text(encoding='utf-8'), 'value = 10\n')
        self.assertEqual(self.b.read_text(encoding='utf-8'), 'value = 2\n')
        print('Rollback also fails -> unresolved reported:', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
