import unittest
from agent_tool_selection import tool_guidance


class ToolRoutingTests(unittest.TestCase):
    def test_calls(self):
        self.assertIn('trace_python_calls', tool_guidance('Which functions call other functions in calculator.py?'))

    def test_local_modules(self):
        self.assertIn('trace_local_imports', tool_guidance('Inspect relationships between local Python modules.'))

    def test_both(self):
        guidance = tool_guidance('Analyze function calls and local module dependencies')
        self.assertIn('trace_python_calls', guidance)
        self.assertIn('trace_local_imports', guidance)

    def test_definitions(self):
        self.assertIn('find_python_symbols', tool_guidance('Locate the definition of add_numbers'))

    def test_no_empty_symbol_search(self):
        self.assertIn('nonempty', tool_guidance('Find class definition'))

    def test_syntax(self):
        self.assertIn('verify_python', tool_guidance('Check syntax errors in app.py'))

    def test_git(self):
        self.assertIn('get_git_status', tool_guidance('Show git status'))

    def test_general(self):
        self.assertIn('read_file', tool_guidance('Explain this project'))

    def test_approvals(self):
        self.assertIn('human-approval', tool_guidance('Edit calculator.py'))

    def test_invalid(self):
        self.assertEqual('', tool_guidance(None))


if __name__ == '__main__':
    unittest.main()
