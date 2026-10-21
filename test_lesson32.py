"""Offline readiness regression tests: no API calls and no edits to agent.py."""
import tempfile
import unittest
from pathlib import Path
from lesson32_readiness import create_fixture, run_fixture_tests, evaluate, allowed


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = create_fixture(Path(self.temp.name) / 'fixture')

    def test_discover_buggy_module(self):
        self.assertTrue(evaluate(self.root, allowed)['discounts_discovered'])

    def test_discover_caller(self):
        self.assertTrue(evaluate(self.root, allowed)['pricing_discovered'])

    def test_bug_reproduced(self):
        result = run_fixture_tests(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('FAIL', result.stderr)

    def test_fixture_passes_after_simulated_approved_fix(self):
        p = self.root / 'discounts.py'
        p.write_text(p.read_text(encoding='utf-8').replace('percent / 10', 'percent / 100'), encoding='utf-8')
        result = run_fixture_tests(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_source_change_during_investigation(self):
        before = {p.name: p.read_bytes() for p in self.root.glob('*.py')}
        evaluate(self.root, allowed)
        after = {p.name: p.read_bytes() for p in self.root.glob('*.py')}
        self.assertEqual(before, after)

    def test_outside_path_blocked(self):
        self.assertFalse(allowed(self.root, '../outside.py'))

    def test_fixture_uses_standard_library_only(self):
        self.assertNotIn('pip install', (self.root / 'test_pricing.py').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
