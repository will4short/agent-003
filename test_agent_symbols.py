import tempfile
import unittest
from pathlib import Path
from agent_symbols import search_python_symbols, python_module_imports


def safe(root, name):
    p = (Path(root) / name).resolve()
    return p.is_relative_to(Path(root).resolve()) and p.suffix == '.py'


class SymbolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'sample.py').write_text('import os\nfrom . import helper\nclass Demo:\n    def run(self):\n        pass\nasync def runner():\n    pass\n', encoding='utf-8')

    def test_function_search(self):
        self.assertEqual(search_python_symbols(self.root, 'run', safe)['matches'][0]['name'], 'Demo.run')

    def test_class_search(self):
        self.assertEqual(search_python_symbols(self.root, 'demo', safe)['matches'][0]['kind'], 'class')

    def test_async_search(self):
        self.assertEqual(search_python_symbols(self.root, 'runner', safe)['matches'][0]['kind'], 'async function')

    def test_imports(self):
        r = python_module_imports(self.root, 'sample.py', safe)
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(len(r['imports']), 2)

    def test_path_escape(self):
        self.assertEqual(python_module_imports(self.root, '../other.py', safe)['status'], 'BLOCKED')

    def test_no_code_execution(self):
        (self.root / 'evil.py').write_text('raise RuntimeError("executed")\ndef harmless(): pass\n')
        self.assertEqual(search_python_symbols(self.root, 'harmless', safe)['status'], 'OK')

    def test_invalid_query(self):
        self.assertEqual(search_python_symbols(self.root, '', safe)['status'], 'BLOCKED')

    def test_symlink_excluded(self):
        link = self.root / 'linked.py'
        try:
            link.symlink_to(self.root / 'sample.py')
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unavailable')
        self.assertEqual(python_module_imports(self.root, 'linked.py', safe)['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
