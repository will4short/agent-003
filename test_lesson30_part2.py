"""Offline tests: safe diagnostics and structural approval-gate regression checks.

These tests do NOT execute agent.py, run project tests, or invoke the API.
"""
import ast
import unittest
from pathlib import Path
from agent_safe_errors import safe_tool_error

ROOT = Path(__file__).resolve().parent


def source_tree():
    return ast.parse((ROOT / 'agent.py').read_text(encoding='utf-8'))


def method(name):
    matches = [n for n in ast.walk(source_tree()) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    if len(matches) != 1:
        raise AssertionError(f'Expected exactly one {name} function, found {len(matches)}')
    return matches[0]


def calls(node, function):
    return [n for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == function]


class SafeErrorTests(unittest.TestCase):
    def test_missing_argument_redacted(self):
        result = safe_tool_error('read_file', KeyError('PRIVATE_API_KEY'))
        self.assertEqual(result['status'], 'ERROR')
        self.assertEqual(result['error_type'], 'KeyError')
        self.assertNotIn('PRIVATE_API_KEY', str(result))

    def test_unexpected_exception_redacted(self):
        result = safe_tool_error('run_tests', RuntimeError('secret=/home/private/token'))
        self.assertEqual(result['error_type'], 'UnexpectedError')
        self.assertNotIn('secret', str(result))
        self.assertNotIn('/home/private', str(result))

    def test_tool_name_redacted(self):
        self.assertEqual(safe_tool_error('token=secret', ValueError('bad'))['tool'], 'unknown')

    def test_no_retry_claim(self):
        self.assertFalse(safe_tool_error('read_file', ValueError('bad'))['retry_safe'])


class ApprovalStructureTests(unittest.TestCase):
    def test_single_edit_uses_review(self):
        tree = source_tree()
        self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'review_proposal' for n in ast.walk(tree)))
        self.assertTrue(calls(method('review_proposal'), 'input'))

    def test_multi_edit_uses_review(self):
        self.assertTrue(calls(method('review_multi_edit'), 'input'))

    def test_recovery_uses_review(self):
        self.assertTrue(calls(method('review_and_apply_recovery'), 'review_proposal'))
        self.assertTrue(calls(method('review_and_apply_recovery'), 'apply_approved_proposal'))

    def test_tests_have_approval_prompt(self):
        self.assertTrue(calls(method('run_project_tests'), 'input'))

    def test_tool_errors_are_structured(self):
        self.assertIn('safe_tool_error(tool_call.name, error)', (ROOT / 'agent.py').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
