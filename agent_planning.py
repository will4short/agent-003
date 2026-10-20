"""Lesson 22: bounded, advisory plans. Never executes or approves actions."""
from dataclasses import dataclass, field

MAX_STEPS = 6

@dataclass
class TaskPlanner:
    steps: list[str] = field(default_factory=list)
    completed: set[int] = field(default_factory=set)

    def create(self, steps):
        if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
            return {'status': 'INVALID', 'message': 'Provide 1 to 6 planning steps.'}
        if any(not isinstance(s, str) or not s.strip() or len(s) > 240 for s in steps):
            return {'status': 'INVALID', 'message': 'Each step must be nonempty and at most 240 characters.'}
        self.steps = [s.strip() for s in steps]
        self.completed = set()
        return {'status': 'PLANNED', 'steps': self.status()['steps'],
                'message': 'Advisory plan only. No files changed and no approval granted.'}

    def complete(self, step_number):
        if type(step_number) is not int or not 1 <= step_number <= len(self.steps):
            return {'status': 'INVALID', 'message': 'Unknown step number.'}
        if any(n not in self.completed for n in range(1, step_number)):
            return {'status': 'BLOCKED', 'message': 'Complete earlier steps first.'}
        self.completed.add(step_number)
        return self.status()

    def status(self):
        return {'status': 'PLAN_STATUS', 'steps': [
            {'number': n, 'description': step, 'done': n in self.completed}
            for n, step in enumerate(self.steps, 1)],
            'message': 'Plan status is advisory, not evidence that tools succeeded.'}
