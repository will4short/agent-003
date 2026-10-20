import unittest
from agent_planning import TaskPlanner

class PlanningTests(unittest.TestCase):
    def setUp(self): self.p = TaskPlanner()
    def test_create(self):
        self.assertEqual(self.p.create(['Inspect', 'Propose'])['status'], 'PLANNED')
        self.assertEqual(len(self.p.status()['steps']), 2)
    def test_reject_empty(self): self.assertEqual(self.p.create([])['status'], 'INVALID')
    def test_reject_many(self): self.assertEqual(self.p.create(['x']*7)['status'], 'INVALID')
    def test_reject_bad_step(self): self.assertEqual(self.p.create([''])['status'], 'INVALID')
    def test_order(self):
        self.p.create(['A','B'])
        self.assertEqual(self.p.complete(2)['status'], 'BLOCKED')
        self.p.complete(1)
        self.assertTrue(self.p.complete(2)['steps'][1]['done'])
    def test_invalid_number(self):
        self.p.create(['A'])
        self.assertEqual(self.p.complete(True)['status'], 'INVALID')
        self.assertEqual(self.p.complete(3)['status'], 'INVALID')
    def test_new_plan_resets(self):
        self.p.create(['A']); self.p.complete(1)
        self.p.create(['B'])
        self.assertFalse(self.p.status()['steps'][0]['done'])

if __name__ == '__main__': unittest.main()
