import unittest
from agent_execution import ExecutionMonitor


class ExecutionMonitorTests(unittest.TestCase):
    def test_warns_only_on_third_identical_read(self):
        monitor = ExecutionMonitor()
        args = {'filename': 'src/main.py'}
        self.assertIsNone(monitor.observe('read_file', args, 'source'))
        self.assertIsNone(monitor.observe('read_file', args, 'source'))
        self.assertIn('identical arguments', monitor.observe('read_file', args, 'source'))
        self.assertIsNone(monitor.observe('read_file', args, 'source'))

    def test_different_arguments_are_independent(self):
        monitor = ExecutionMonitor()
        for name in ['a.py', 'b.py']:
            self.assertIsNone(monitor.observe('read_file', {'filename': name}, 'source'))

    def test_approval_sensitive_tools_are_never_monitored(self):
        monitor = ExecutionMonitor(repetition_threshold=2)
        for _ in range(5):
            self.assertIsNone(monitor.observe('propose_edit', {'filename': 'a.py'}, {}))
            self.assertIsNone(monitor.observe('run_tests', {}, {}))
            self.assertIsNone(monitor.observe('propose_recovery', {}, {}))

    def test_reset_clears_task_history(self):
        monitor = ExecutionMonitor(repetition_threshold=2)
        monitor.observe('list_files', {}, [])
        self.assertIsNotNone(monitor.observe('list_files', {}, []))
        monitor.reset()
        self.assertIsNone(monitor.observe('list_files', {}, []))

    def test_unrecognized_tools_are_not_monitored(self):
        monitor = ExecutionMonitor(repetition_threshold=2)
        self.assertIsNone(monitor.observe('unknown', {}, None))
        self.assertIsNone(monitor.observe('unknown', {}, None))


if __name__ == '__main__':
    unittest.main()
