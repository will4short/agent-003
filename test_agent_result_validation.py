import unittest
from agent_result_validation import validate_tool_result, model_tool_output


class ResultValidationTests(unittest.TestCase):
    def test_success(self):
        self.assertEqual(validate_tool_result('verify_python', {'status': 'PASS'})['quality'], 'SUPPORTED')

    def test_failure(self):
        self.assertEqual(validate_tool_result('verify_python', {'status': 'FAIL'})['quality'], 'FAILED')

    def test_blocked(self):
        self.assertEqual(validate_tool_result('inspect_python_imports', {'status': 'BLOCKED'})['quality'], 'FAILED')

    def test_truncated(self):
        self.assertEqual(validate_tool_result('trace_local_imports', {'status': 'OK', 'truncated': True})['quality'], 'INCOMPLETE')

    def test_static(self):
        self.assertEqual(validate_tool_result('trace_python_calls', {'status': 'OK', 'truncated': False})['quality'], 'STATIC_ONLY')

    def test_unrecognized_status(self):
        self.assertEqual(validate_tool_result('trace_python_calls', {'status': 'SOMETHING'})['quality'], 'UNVERIFIED')

    def test_error_string(self):
        self.assertEqual(validate_tool_result('read_file', 'Tool error: OSError')['quality'], 'FAILED')

    def test_list_is_not_exhaustive(self):
        self.assertEqual(validate_tool_result('list_files', ['a.py'])['quality'], 'UNVERIFIED')

    def test_read_only_wrapped(self):
        raw = {'status': 'OK', 'truncated': True}
        output = model_tool_output('trace_local_imports', raw)
        self.assertEqual(output['tool_result'], raw)
        self.assertEqual(output['evidence_validation']['quality'], 'INCOMPLETE')

    def test_approval_tools_untouched(self):
        for name in ('propose_edit', 'propose_multi_edit', 'propose_recovery', 'run_tests'):
            raw = {'status': 'APPLIED'}
            self.assertIs(model_tool_output(name, raw), raw)

    def test_unknown_tool_untouched(self):
        raw = {'status': 'OK'}
        self.assertIs(model_tool_output('unknown_tool', raw), raw)

    def test_missing_status(self):
        self.assertEqual(validate_tool_result('read_file', {'content': 'x'})['quality'], 'UNVERIFIED')


if __name__ == '__main__':
    unittest.main()
