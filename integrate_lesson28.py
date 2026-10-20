"""Install Lesson 28 validation. Offline, idempotent, fail-closed on unknown layouts."""
import ast
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'agent.py'
MARKER = '# LESSON28_RESULT_VALIDATION'


def integrate():
    if not (ROOT / 'agent_result_validation.py').is_file():
        raise SystemExit('Missing agent_result_validation.py.')
    original = TARGET.read_text(encoding='utf-8')
    if MARKER in original:
        print('Lesson 28 already installed; no changes made.')
        return
    if '# LESSON27_TOOL_ROUTING' not in original:
        raise SystemExit('Lesson 27 must be installed first; no changes made.')
    anchor = '            tool_outputs.append({\n                "type": "function_call_output",'
    if original.count(anchor) != 1:
        raise SystemExit('Unexpected tool-output layout; no changes made.')
    replacement = '''            # LESSON28_RESULT_VALIDATION: advisory metadata for read-only tools only.
            from agent_result_validation import model_tool_output
            validated_output = model_tool_output(tool_call.name, result)
            assessment = validated_output.get('evidence_validation') if isinstance(validated_output, dict) else None
            if assessment:
                print(f"Evidence: {assessment['quality']} — {assessment['guidance']}")

''' + anchor
    updated = original.replace(anchor, replacement)
    output_anchor = '                "output": json.dumps(result),'
    if updated.count(output_anchor) != 1:
        raise SystemExit('Unexpected serialization layout; no changes made.')
    updated = updated.replace(output_anchor, '                "output": json.dumps(validated_output),')
    ast.parse(updated)
    backup = ROOT / 'agent-before-lesson28-integration.bak'
    if backup.exists():
        raise SystemExit('Backup already exists; refusing to overwrite.')
    shutil.copy2(TARGET, backup)
    TARGET.write_text(updated, encoding='utf-8')
    print('Lesson 28 installed. Backup:', backup.name)


if __name__ == '__main__':
    integrate()
