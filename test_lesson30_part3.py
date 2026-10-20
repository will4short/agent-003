"""Lesson 30 Part 3: offline approval-boundary behavioral regression tests.

Run: python -m unittest test_lesson30_part3 -v
Loads selected function definitions from agent.py without importing/running its CLI.
No API requests, shell commands, project edits, or real test execution.
"""
import ast
import builtins
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

AGENT = Path(__file__).resolve().with_name('agent.py')
NAMES = {'review_proposal', 'review_multi_edit', 'run_project_tests',
         'review_and_apply_recovery', 'propose_edit', 'propose_multi_edit'}


def load_functions():
    tree = ast.parse(AGENT.read_text(encoding='utf-8'), filename=str(AGENT))
    selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name in NAMES]
    present = {node.name for node in selected}
    missing = NAMES - present
    if missing:
        raise AssertionError(f'Missing required functions: {sorted(missing)}')
    namespace = {'__file__': str(AGENT), 'Path': Path, 'subprocess': Mock(), 'sys': Mock(),
                 'is_safe_project_file': lambda root, filename: True,
                 'file_hash': lambda content: __import__('hashlib').sha256(content.encode()).hexdigest(),
                 'difflib': __import__('difflib'), 'MULTI_EDIT_LIMIT': 5}
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(AGENT), 'exec'), namespace)
    return namespace


class ApprovalBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fn = load_functions()

    def test_single_edit_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / 'example.py'
            target.write_text('original\n', encoding='utf-8')
            proposal = self.fn['propose_edit'](root, 'example.py', 'changed\n')
            self.assertEqual(proposal['status'], 'PENDING')
            with patch.object(builtins, 'input', return_value='REJECT'):
                decision = self.fn['review_proposal'](proposal)
            self.assertEqual(decision['decision'], 'REJECT')
            self.assertEqual(target.read_text(encoding='utf-8'), 'original\n')

    def test_single_edit_revision_not_approval(self):
        proposal = {'diff': 'mock diff'}
        with patch.object(builtins, 'input', side_effect=['REVISE', 'Please adjust']):
            decision = self.fn['review_proposal'](proposal)
        self.assertEqual(decision['decision'], 'REVISE')

    def test_multi_edit_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for filename in ('a.py', 'b.py'):
                (root / filename).write_text('original\n', encoding='utf-8')
            proposal = self.fn['propose_multi_edit'](root, [
                {'filename': 'a.py', 'new_content': 'new a\n'},
                {'filename': 'b.py', 'new_content': 'new b\n'}])
            self.assertEqual(proposal['status'], 'PENDING')
            with patch.object(builtins, 'input', return_value='REJECT'):
                decision = self.fn['review_multi_edit'](proposal)
            self.assertEqual(decision['decision'], 'REJECT')
            for filename in ('a.py', 'b.py'):
                self.assertEqual((root / filename).read_text(encoding='utf-8'), 'original\n')

    def test_tests_outside_disposable_project_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(builtins, 'input', side_effect=AssertionError('Must not prompt')):
                result = self.fn['run_project_tests'](Path(temp))
            self.assertEqual(result['status'], 'BLOCKED')
            self.fn['run_project_tests'].__globals__['subprocess'].run.assert_not_called()

    def test_tests_rejected_without_execution(self):
        disposable = AGENT.parent / 'test-project'
        subprocess_stub = Mock()
        self.fn['run_project_tests'].__globals__['subprocess'] = subprocess_stub
        for answer in ('NO', 'APPROVE', '', 'yes'):
            with self.subTest(answer=answer), patch.object(builtins, 'input', return_value=answer):
                result = self.fn['run_project_tests'](disposable)
                self.assertEqual(result['status'], 'REJECTED')
        subprocess_stub.run.assert_not_called()

    def test_recovery_rejected_without_application(self):
        namespace = self.fn['review_and_apply_recovery'].__globals__
        proposal = {'status': 'PENDING', 'diff': 'rollback proposal'}
        with patch.dict(namespace, {
            'propose_recovery': lambda root, recovery: proposal,
            'review_proposal': lambda p: {'decision': 'REJECT'},
            'apply_approved_proposal': Mock(side_effect=AssertionError('Unauthorized write')),
        }):
            result = self.fn['review_and_apply_recovery'](Path('.'), {'filename': 'x.py'})
            self.assertEqual(result['status'], 'REJECTED')
            namespace['apply_approved_proposal'].assert_not_called()

    def test_recovery_revision_without_application(self):
        namespace = self.fn['review_and_apply_recovery'].__globals__
        with patch.dict(namespace, {
            'propose_recovery': lambda root, recovery: {'status': 'PENDING'},
            'review_proposal': lambda p: {'decision': 'REVISE', 'feedback': 'No'},
            'apply_approved_proposal': Mock(side_effect=AssertionError('Unauthorized write')),
        }):
            result = self.fn['review_and_apply_recovery'](Path('.'), {'filename': 'x.py'})
            self.assertEqual(result['status'], 'REVISION_REQUESTED')
            namespace['apply_approved_proposal'].assert_not_called()

    def test_dispatch_approval_gate_structure(self):
        tree = ast.parse(AGENT.read_text(encoding='utf-8'))
        source = AGENT.read_text(encoding='utf-8')
        for token in ('review_proposal(proposal)', 'review_multi_edit(proposal)',
                      'review_and_apply_recovery(PROJECT_ROOT, last_recovery)',
                      'run_project_tests(PROJECT_ROOT)'):
            self.assertIn(token, source)
        self.assertIsInstance(tree, ast.Module)


if __name__ == '__main__':
    unittest.main()
