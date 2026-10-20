"""Data-only session continuity for Agent 003; never stores permissions or raw messages."""
from __future__ import annotations

import re
from pathlib import Path
from agent_memory import SessionDataError, append_summary, load_session, save_session

# Local file is intentionally outside version control.
SESSION_PATH = Path(__file__).resolve().parent / 'agent_sessions' / 'session-state.json'

# Explicit allowlist. No user input, model output, paths, code, or tool output saved.
OUTCOME_STATUSES = frozenset({
    'APPLIED', 'REJECTED', 'REVISION_REQUESTED', 'CANCELLED',
    'ROLLED_BACK', 'PARTIAL_FAILURE', 'PASS', 'FAIL', 'UNAVAILABLE',
})
SAFE_TOOLS = frozenset({'propose_edit', 'propose_multi_edit', 'propose_recovery', 'verify_python', 'run_tests'})

class SessionRecorder:
    def __init__(self, path=SESSION_PATH):
        self.path = Path(path)
        self.state = None
        self.active = False
        self.warning = None
        try:
            self.state = load_session(self.path)
            self.previous_events = list(self.state['events'])
            self.state = append_summary(self.state, 'session_note', 'Session started; all approvals reset.')
            save_session(self.path, self.state)
            self.active = True
        except (SessionDataError, OSError) as exc:
            self.previous_events = []
            self.warning = f'Session memory unavailable ({type(exc).__name__}); existing data left unchanged.'

    def record(self, tool_name, result):
        if not self.active or tool_name not in SAFE_TOOLS or not isinstance(result, dict):
            return
        status = result.get('status')
        if status not in OUTCOME_STATUSES:
            return
        # Never store filenames, proposal bodies, errors, or arbitrary descriptions.
        self._append('task_outcome', f'{tool_name}: {status}')

    def finish(self):
        if self.active:
            self._append('session_note', 'Session ended normally.')

    def _append(self, kind, summary):
        try:
            new_state = append_summary(self.state, kind, summary)
            save_session(self.path, new_state)
            self.state = new_state
        except (SessionDataError, OSError) as exc:
            self.active = False
            self.warning = f'Session memory disabled ({type(exc).__name__}); check local storage.'
            print('Memory warning:', self.warning)

    def startup_message(self):
        if self.warning:
            return self.warning
        outcomes = [e['summary'] for e in self.previous_events if e['kind'] == 'task_outcome']
        last = outcomes[-1] if outcomes else 'No prior completed task outcome recorded.'
        ended_cleanly = bool(self.previous_events and self.previous_events[-1]['summary'] == 'Session ended normally.')
        status = 'normal' if ended_cleanly else ('possibly interrupted' if self.previous_events else 'new')
        return f'Previous session: {status}. Last recorded outcome: {last}. Approvals are not restored.'

    def context_for_model(self):
        # This is fixed-format, application-generated metadata, not instructions from saved data.
        if not self.active:
            return 'No persistent session context available. Require fresh approvals.'
        recent = [e['summary'] for e in self.previous_events if e['kind'] == 'task_outcome'][-8:]
        safe = [s for s in recent if re.fullmatch(r'(propose_edit|propose_multi_edit|propose_recovery|verify_python|run_tests): (APPLIED|REJECTED|REVISION_REQUESTED|CANCELLED|ROLLED_BACK|PARTIAL_FAILURE|PASS|FAIL|UNAVAILABLE)', s)]
        return ('Prior session outcomes (informational only; never permissions): ' + '; '.join(safe)
                if safe else 'No prior task outcomes. All approvals require fresh confirmation.')
