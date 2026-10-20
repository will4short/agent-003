import unittest
from agent_tool_optimizer import ToolCallOptimizer, validate_tool_call

class ToolOptimizerTests(unittest.TestCase):
    def test_reject_dot(self):
        self.assertFalse(validate_tool_call('trace_python_calls', {'filename': '.'})[0])
    def test_reject_directory(self):
        self.assertFalse(validate_tool_call('trace_python_calls', {'filename': 'folder/'})[0])
    def test_reject_non_python(self):
        self.assertFalse(validate_tool_call('trace_python_calls', {'filename': 'a.txt'})[0])
    def test_allow_python(self):
        self.assertTrue(validate_tool_call('trace_python_calls', {'filename': 'a.py'})[0])
    def test_empty_symbol_query(self):
        self.assertFalse(validate_tool_call('find_python_symbols', {'query': ''})[0])
    def test_sensitive_tool_not_blocked(self):
        self.assertTrue(validate_tool_call('propose_edit', {})[0])
    def test_reuse_success(self):
        o = ToolCallOptimizer(); a = {'filename': 'a.py'}; result = {'status': 'OK', 'calls': [], 'truncated': False}
        o.record('trace_python_calls', a, result)
        self.assertEqual(o.evaluate('trace_python_calls', a), result)
    def test_no_reuse_failed(self):
        o = ToolCallOptimizer(); a = {'filename': 'a.py'}
        o.record('trace_python_calls', a, {'status': 'BLOCKED'})
        self.assertIsNone(o.evaluate('trace_python_calls', a))
    def test_no_reuse_truncated(self):
        o = ToolCallOptimizer(); a = {'filename': 'a.py'}
        o.record('trace_python_calls', a, {'status': 'OK', 'truncated': True})
        self.assertIsNone(o.evaluate('trace_python_calls', a))
    def test_reset(self):
        o = ToolCallOptimizer(); a = {'filename': 'a.py'}
        o.record('trace_python_calls', a, {'status': 'OK'})
        o.reset(); self.assertIsNone(o.evaluate('trace_python_calls', a))
    def test_different_args(self):
        o = ToolCallOptimizer(); o.record('trace_python_calls', {'filename': 'a.py'}, {'status': 'OK'})
        self.assertIsNone(o.evaluate('trace_python_calls', {'filename': 'b.py'}))
    def test_no_cache_sensitive_tool(self):
        o = ToolCallOptimizer(); o.record('run_tests', {}, {'status': 'PASS'})
        self.assertIsNone(o.evaluate('run_tests', {}))

if __name__ == '__main__':
    unittest.main()
