#!/usr/bin/env python3
"""Fill in `ActionIndex` on the Shortcuts import questions of a compiled shortcut.

Cherri emits `WFWorkflowImportQuestions` entries with `ParameterKey`/`Text`/
`DefaultValue` but leaves `ActionIndex` out (its value is 0-based and Go's
`omitempty` drops it). Shortcuts silently ignores a question that has no
`ActionIndex`, so importing such a build never shows the prompt.

Cherri blanks the target action's argument value, so the action that receives
the answer is an empty `gettext` action immediately followed by the
`setvariable` action that stores it. We locate that pair by variable name and
write the action index into every import question.

Usage:
    python3 scripts/patch_import_questions.py <shortcut> [--variable apiKey] [--output PATH]
"""

from __future__ import annotations

import plistlib
import sys
from pathlib import Path

GET_TEXT = "is.workflow.actions.gettext"
SET_VARIABLE = "is.workflow.actions.setvariable"


def patch(shortcut: Path, variable: str = "apiKey", output: Path | None = None) -> None:
    with shortcut.open("rb") as handle:
        data = plistlib.load(handle)

    questions = data.get("WFWorkflowImportQuestions") or []
    if not questions:
        raise SystemExit(f"{shortcut}: 没有任何导入问题，先确认源码里有 #question")

    actions = data.get("WFWorkflowActions") or []
    targets = []
    for index, action in enumerate(actions):
        if action.get("WFWorkflowActionIdentifier") != GET_TEXT:
            continue
        if action.get("WFWorkflowActionParameters", {}).get("WFTextActionText") != "":
            continue
        following = actions[index + 1] if index + 1 < len(actions) else {}
        if following.get("WFWorkflowActionIdentifier") != SET_VARIABLE:
            continue
        if following.get("WFWorkflowActionParameters", {}).get("WFVariableName") == variable:
            targets.append(index)
    if len(targets) != 1:
        raise SystemExit(
            f"{shortcut}: 期望恰好 1 个空 gettext + setvariable({variable}) 的导入问题落点，"
            f"实际找到 {len(targets)} 个"
        )

    target = targets[0]
    for question in questions:
        question["ActionIndex"] = target

    destination = output or shortcut
    with destination.open("wb") as handle:
        plistlib.dump(data, handle, fmt=plistlib.FMT_BINARY)
    print(f"patched {len(questions)} import question(s) -> ActionIndex={target}: {destination}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        raise SystemExit(__doc__)
    shortcut_path = Path(argv.pop(0))
    variable = "apiKey"
    output_path: Path | None = None
    while argv:
        flag = argv.pop(0)
        if flag == "--variable" and argv:
            variable = argv.pop(0)
        elif flag == "--output" and argv:
            output_path = Path(argv.pop(0))
        else:
            raise SystemExit(f"unknown argument: {flag}")
    patch(shortcut_path, variable, output_path)
