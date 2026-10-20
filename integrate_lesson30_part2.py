"""Install Lesson 30 Part 2 conservatively; backup and syntax-check before writing."""
from pathlib import Path
import ast
import shutil

root = Path(__file__).resolve().parent
path = root / 'agent.py'
source = path.read_text(encoding='utf-8')
marker = 'from agent_safe_errors import safe_tool_error  # LESSON30_PART2'
if marker in source:
    print('Lesson 30 Part 2 already installed.')
    raise SystemExit(0)
anchor = '            except Exception as error:\n                result = f"Tool error: {type(error).__name__}"'
if source.count(anchor) != 1:
    raise SystemExit('Integration anchor not found exactly once; agent.py unchanged.')
replacement = ('            except Exception as error:\n'
               '                result = safe_tool_error(tool_call.name, error)')
updated = source.replace(anchor, replacement, 1)
updated = updated.replace('from agent_tool_optimizer import ToolCallOptimizer',
                          marker + '\nfrom agent_tool_optimizer import ToolCallOptimizer', 1)
if marker not in updated:
    raise SystemExit('Import anchor missing; agent.py unchanged.')
ast.parse(updated, filename='agent.py')
backup = root / 'agent-before-lesson30-part2.bak'
if backup.exists():
    raise SystemExit('Backup already exists; refusing to overwrite.')
shutil.copy2(path, backup)
path.write_text(updated, encoding='utf-8')
print('Lesson 30 Part 2 installed. Backup:', backup.name)
