import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "Jev_Clipboard_Guard.cherri").read_text(encoding="utf-8")
CASES = json.loads((ROOT / "tests" / "share-rule-cases.json").read_text(encoding="utf-8"))


def share_patterns():
    block = SOURCE.split('@shareType = ""', 1)[1].split('if @shareType != ""', 1)[0]
    return [pattern for pattern in re.findall(r"matchText\('((?:\\.|[^'])*)', @clip\)", block)]


class ShareRuleTests(unittest.TestCase):
    def test_share_fixtures_are_recognized_by_a_local_pattern(self):
        patterns = [re.compile(p) for p in share_patterns()]
        self.assertGreaterEqual(len(patterns), 8, "Expected platform-specific local share patterns")
        for case in CASES:
            with self.subTest(case=case["name"]):
                self.assertTrue(any(pattern.search(case["text"]) for pattern in patterns))

    def test_ordinary_text_is_not_classified_as_share_content(self):
        patterns = [re.compile(p) for p in share_patterns()]
        ordinary = [
            "今天午饭吃什么？",
            "Please review this paragraph before the meeting.",
            "const value = 42;",
        ]
        for text in ordinary:
            with self.subTest(text=text):
                self.assertFalse(any(pattern.search(text) for pattern in patterns))

    def test_cross_app_shopping_allowlist_is_present(self):
        match = re.search(r"@trustedShoppingConsumer = matchText\('([^']+)'", SOURCE)
        self.assertIsNotNone(match)
        allowlist = re.compile(match.group(1))
        for name in ("慢慢买", "什么值得买", "惠惠购物助手", "比价狗"):
            with self.subTest(name=name):
                self.assertTrue(allowlist.search(name))
        self.assertFalse(allowlist.search("照片编辑器"))


if __name__ == "__main__":
    unittest.main()
