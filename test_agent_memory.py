import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_memory import (SessionDataError, append_summary, load_session,
                          new_session, save_session)


class SessionMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "agent_sessions" / "session-state.json"

    def test_missing_file_creates_new_in_memory_state(self):
        state = load_session(self.path)
        self.assertEqual(state["events"], [])
        self.assertFalse(self.path.exists())

    def test_round_trip(self):
        state = append_summary(new_session(), "task_outcome", "8 tests passed")
        save_session(self.path, state)
        self.assertEqual(load_session(self.path), state)

    def test_corrupt_json_is_preserved(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(SessionDataError):
            load_session(self.path)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{not json")

    def test_unexpected_approval_fields_are_rejected(self):
        state = new_session()
        state["approval"] = "APPROVE"
        with self.assertRaises(SessionDataError):
            save_session(self.path, state)
        self.assertFalse(self.path.exists())

    def test_executable_event_fields_are_rejected(self):
        state = new_session()
        state["events"].append({"kind": "task_outcome", "summary": "pending",
                                "timestamp": "now", "tool_call": "apply_edit"})
        with self.assertRaises(SessionDataError):
            save_session(self.path, state)

    def test_unsupported_schema_is_rejected(self):
        state = new_session()
        state["schema_version"] = 99
        self.path.parent.mkdir(parents=True)
        self.path.write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(SessionDataError):
            load_session(self.path)

    def test_event_count_is_bounded(self):
        state = new_session()
        for i in range(110):
            state = append_summary(state, "session_note", str(i))
        self.assertEqual(len(state["events"]), 100)
        self.assertEqual(state["events"][0]["summary"], "10")

    def test_failed_replace_preserves_previous_file(self):
        save_session(self.path, new_session())
        original = self.path.read_bytes()
        with patch("agent_memory.os.replace", side_effect=OSError("simulated")):
            with self.assertRaises(OSError):
                save_session(self.path, append_summary(new_session(), "session_note", "new"))
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
