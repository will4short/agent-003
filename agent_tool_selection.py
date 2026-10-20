"""Lesson 27: bounded, advisory tool routing for each user task.

This module never executes tools, changes files, or grants approvals.
"""
import re


def tool_guidance(goal: str) -> str:
    """Return concise, task-specific guidance for the model's existing tools."""
    if not isinstance(goal, str):
        return ''
    words = goal.casefold()[:4000]
    guidance = []
    if re.search(r'\b(call graph|calls? (?:other )?functions?|function calls?|who calls|call relationships?|calling relationships?)\b', words):
        guidance.append('For function-call relationships, use trace_python_calls on relevant Python files FIRST; do not substitute symbol search or full-file reads unless needed.')
    if re.search(r'\b(local (?:python )?modules?|module (?:dependencies|relationships?|imports?)|dependency graph|dependencies between|import graph|circular imports?)\b', words):
        guidance.append('For relationships between local Python modules, use trace_local_imports FIRST; inspect_python_imports is for imports within one specific file.')
    if re.search(r'\b(find|locate|where|definition|defined|symbol|method|class)\b', words) and not guidance:
        guidance.append('For locating Python definitions, use find_python_symbols with a nonempty specific name; never call it with an empty query.')
    if re.search(r'\b(syntax|compile|syntax errors?)\b', words):
        guidance.append('For Python syntax checks, prefer verify_python; syntax verification is not a behavioral test.')
    if re.search(r'\b(git status|working tree|uncommitted|git diff|changed files)\b', words):
        guidance.append('For repository status/diffs, use get_git_status or get_git_diff instead of reading source files.')
    if not guidance:
        guidance.append('Select the smallest relevant existing read-only tool; read_file only when actual source content is required.')
    guidance.append('Avoid redundant tool calls and unnecessary planning for simple read-only questions. For edits, tests, and recovery, preserve ALL existing explicit human-approval gates; these suggestions authorize nothing.')
    return ' LESSON27 TOOL ROUTING (advisory): ' + ' '.join(guidance)
