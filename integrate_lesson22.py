"""Install Lesson 22 into the Lesson 21 agent. Run from agent-003 folder."""
from pathlib import Path
import shutil

path = Path('agent.py')
source = path.read_text(encoding='utf-8')
marker = '# LESSON22_PLANNING_INTEGRATION'
if marker in source:
    print('Lesson 22 already installed; no changes made.')
    raise SystemExit(0)
if 'from agent_cost import CostGuard, BudgetExceeded' not in source:
    raise SystemExit('Expected Lesson 21 agent.py; no changes made.')
if not Path('agent_planning.py').is_file():
    raise SystemExit('Place agent_planning.py in this folder first.')

anchor = 'tools = [\n'
if source.count(anchor) != 1:
    raise SystemExit('Could not safely locate tools list; no changes made.')
addition = '''# LESSON22_PLANNING_INTEGRATION: advisory plan tools, never authorization.
PLAN_TOOL_DEFINITIONS = [
    {
        "type": "function", "name": "create_task_plan",
        "description": "Create a short advisory plan before a multi-step coding task. Does not change files or grant approval.",
        "parameters": {"type": "object", "properties": {"steps": {
            "type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 6}},
            "required": ["steps"], "additionalProperties": False}, "strict": True,
    },
    {
        "type": "function", "name": "complete_plan_step",
        "description": "Mark a planning step complete ONLY after verifying the corresponding action succeeded.",
        "parameters": {"type": "object", "properties": {"step_number": {"type": "integer"}},
            "required": ["step_number"], "additionalProperties": False}, "strict": True,
    },
    {
        "type": "function", "name": "get_task_plan",
        "description": "Get the current advisory plan and completion state.",
        "parameters": {"type": "object", "properties": {}, "required": [],
            "additionalProperties": False}, "strict": True,
    },
]
'''
source = source.replace(anchor, addition + '\n' + anchor, 1)
anchor2 = 'PROJECT_ROOT = select_project()'
if source.count(anchor2) != 1:
    raise SystemExit('Could not locate project selection; no changes made.')
source = source.replace(anchor2, '''from agent_planning import TaskPlanner
# LESSON22: register planning tools without modifying existing tool definitions.
tools.extend(PLAN_TOOL_DEFINITIONS)
task_planner = TaskPlanner()

''' + anchor2, 1)
anchor3 = '                if tool_call.name == "list_files":'
if source.count(anchor3) != 1:
    raise SystemExit('Could not locate dispatch; no changes made.')
source = source.replace(anchor3, '''                if tool_call.name == "create_task_plan":
                    result = task_planner.create(arguments["steps"])

                elif tool_call.name == "complete_plan_step":
                    result = task_planner.complete(arguments["step_number"])

                elif tool_call.name == "get_task_plan":
                    result = task_planner.status()

                elif tool_call.name == "list_files":''', 1)
anchor4 = '    "Do not execute application code or arbitrary shell commands. "'
if source.count(anchor4) != 1:
    raise SystemExit('Could not locate instructions; no changes made.')
source = source.replace(anchor4, '''    "For nontrivial multi-step tasks, first use create_task_plan with 2 to 6 concise steps. "
    "Use get_task_plan to inspect progress and complete_plan_step only after verified results. "
    "Plans are advisory; they never replace human approval for edits or tests. "
    "Do not claim a step succeeded without a successful tool result. "
''' + anchor4, 1)
compile(source, str(path), 'exec')
backup = Path('agent-before-lesson22-integration.bak')
if backup.exists():
    raise SystemExit('Backup already exists; refusing to overwrite. No changes made.')
shutil.copy2(path, backup)
path.write_text(source, encoding='utf-8')
print('Lesson 22 installed. Backup:', backup)
