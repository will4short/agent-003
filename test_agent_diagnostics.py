import unittest
from agent_diagnostics import diagnose_failure


class DiagnosticTests(unittest.TestCase):
    def test_syntax(self):
        result = diagnose_failure('verify_python', {'status': 'FAIL', 'message': 'SyntaxError: invalid syntax'})
        self.assertEqual(result['status'], 'DIAGNOSIS')
        self.assertIn('syntax', result['findings'][0]['possible_cause'].lower())

    def test_assertion(self):
        result = diagnose_failure('run_tests', {'status': 'FAIL', 'output': 'AssertionError: 1 != 2'})
        self.assertIn('assertion', result['findings'][0]['possible_cause'].lower())

    def test_import(self):
        result = diagnose_failure('run_tests', {'status': 'FAIL', 'output': 'ModuleNotFoundError: missing'})
        self.assertIn('Import', result['findings'][0]['possible_cause'])

    def test_unknown(self):
        result = diagnose_failure('run_tests', {'status': 'FAIL', 'output': 'something unexpected'})
        self.assertEqual(result['findings'][0]['possible_cause'], 'Unclassified failure')

    def test_pass_rejected(self):
        self.assertEqual(diagnose_failure('run_tests', {'status': 'PASS'})['status'], 'UNAVAILABLE')

    def test_unsupported_tool(self):
        self.assertEqual(diagnose_failure('read_file', {'status': 'FAIL'})['status'], 'UNAVAILABLE')

    def test_no_arbitrary_output_echo(self):
        result = diagnose_failure('run_tests', {'status': 'FAIL', 'output': 'API_KEY=SECRET123\nNameError'})
        self.assertNotIn('SECRET123', str(result))

    def test_location_is_bounded(self):
        result = diagnose_failure('verify_python', {'status': 'FAIL', 'message': 'File "C:\\work\\hello.py", line 9\nSyntaxError'})
        self.assertEqual(result['locations'], [{'file': 'hello.py', 'line': 9}])


if __name__ == '__main__':
    unittest.main()
