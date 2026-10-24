import plistlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from patch_import_questions import patch  # noqa: E402

GET_TEXT = "is.workflow.actions.gettext"
SET_VARIABLE = "is.workflow.actions.setvariable"


def build_shortcut(actions, questions):
    return {
        "WFWorkflowActions": actions,
        "WFWorkflowImportQuestions": questions,
    }


def gettext(text):
    return {
        "WFWorkflowActionIdentifier": GET_TEXT,
        "WFWorkflowActionParameters": {"WFTextActionText": text},
    }


def setvariable(name):
    return {
        "WFWorkflowActionIdentifier": SET_VARIABLE,
        "WFWorkflowActionParameters": {"WFVariableName": name},
    }


class PatchImportQuestionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "shortcut"
        self.output = Path(self.tmp.name) / "patched"

    def write(self, data):
        self.path.write_bytes(plistlib.dumps(data, fmt=plistlib.FMT_BINARY))

    def test_fills_action_index_of_question_target(self):
        self.write(
            build_shortcut(
                [gettext("https://example.com"), setvariable("apiUrl"), gettext(""), setvariable("apiKey")],
                [{"ParameterKey": "WFTextActionText", "Category": "Parameter", "Text": "请输入 Key"}],
            )
        )

        patch(self.path, "apiKey", self.output)

        data = plistlib.loads(self.output.read_bytes())
        self.assertEqual(data["WFWorkflowImportQuestions"][0]["ActionIndex"], 2)

    def test_ignores_empty_gettext_belonging_to_other_variable(self):
        self.write(
            build_shortcut(
                [gettext(""), setvariable("shareType"), gettext(""), setvariable("apiKey")],
                [{"ParameterKey": "WFTextActionText", "Category": "Parameter"}],
            )
        )

        patch(self.path, "apiKey", self.output)

        data = plistlib.loads(self.output.read_bytes())
        self.assertEqual(data["WFWorkflowImportQuestions"][0]["ActionIndex"], 2)

    def test_rejects_build_without_import_questions(self):
        self.write(build_shortcut([gettext("")], []))

        with self.assertRaises(SystemExit):
            patch(self.path, "apiKey", self.output)

    def test_rejects_ambiguous_target(self):
        self.write(
            build_shortcut(
                [gettext(""), setvariable("apiKey"), gettext(""), setvariable("apiKey")],
                [{"ParameterKey": "WFTextActionText", "Category": "Parameter"}],
            )
        )

        with self.assertRaises(SystemExit):
            patch(self.path, "apiKey", self.output)


if __name__ == "__main__":
    unittest.main()
