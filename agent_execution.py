"""Advisory investigation-progress monitor for Agent 003.

Only observes read-only calls. It never intercepts approval-sensitive operations,
changes project files, or ends the model loop on its own.
"""
import json
from collections import Counter

OBSERVED_TOOLS = frozenset({
    'read_file', 'list_files', 'search_code', 'find_python_symbols',
    'inspect_python_imports', 'trace_python_calls', 'trace_local_imports',
    'trace_web_imports', 'investigate_project', 'get_git_status', 'get_git_diff',
})


class ExecutionMonitor:
    def __init__(self, repetition_threshold=3):
        if repetition_threshold < 2:
            raise ValueError('repetition_threshold must be at least 2')
        self.repetition_threshold = repetition_threshold
        self.reset()

    def reset(self):
        self._counts = Counter()
        self._warnings = set()

    def observe(self, name, arguments, result):
        """Return advisory text only for repeated equivalent read-only requests.

        The original result is always delivered to the model. Repetition is
        measured within the current task, not across independent user tasks.
        """
        if name not in OBSERVED_TOOLS or not isinstance(arguments, dict):
            return None
        key = (name, json.dumps(arguments, sort_keys=True, default=str))
        self._counts[key] += 1
        count = self._counts[key]
        if count < self.repetition_threshold or key in self._warnings:
            return None
        self._warnings.add(key)
        return (
            f'You have requested {name} with identical arguments {count} times '
            'during this task. Review the evidence already returned. If enough '
            'information is available, give the user a concise final answer. '
            'Otherwise, identify the specific missing evidence and use a different '
            'targeted read-only investigation. Do not skip approvals for edits, '
            'test execution, or recovery.'
        )
