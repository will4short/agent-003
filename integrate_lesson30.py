"""Install Lesson 30 safely; run from the agent-003 repository directory."""
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parent
agent = root / 'agent.py'
module = root / 'agent_cache_hardening.py'
if not agent.is_file() or not module.is_file():
    sys.exit('ERROR: agent.py and agent_cache_hardening.py must be in this folder.')
original = agent.read_text(encoding='utf-8')
marker = 'from agent_cache_hardening import FileAwareToolCallOptimizer as ToolCallOptimizer  # LESSON30_CACHE_HARDENING'
if marker in original:
    print('Lesson 30 already installed; no changes made.')
    sys.exit(0)
anchor = 'tool_optimizer = ToolCallOptimizer()'
if original.count(anchor) != 1:
    sys.exit('ERROR: Expected Lesson 29 optimizer initialization exactly once. No changes made.')
if 'from agent_tool_optimizer import ToolCallOptimizer, TOOL_EFFICIENCY_GUIDANCE' not in original:
    sys.exit('ERROR: Lesson 29 optimizer import not found. No changes made.')
updated = original.replace(anchor, 'tool_optimizer = ToolCallOptimizer(PROJECT_ROOT)', 1)
updated = updated.replace('tool_optimizer = ToolCallOptimizer(PROJECT_ROOT)', marker + '\ntool_optimizer = ToolCallOptimizer(PROJECT_ROOT)', 1)
compile(updated, str(agent), 'exec')
backup = root / 'agent-before-lesson30-integration.bak'
if backup.exists():
    sys.exit('ERROR: Backup already exists; inspect it before retrying. No changes made.')
shutil.copy2(agent, backup)
try:
    agent.write_text(updated, encoding='utf-8')
except OSError:
    shutil.copy2(backup, agent)
    raise
print('Lesson 30 installed. Backup:', backup.name)
