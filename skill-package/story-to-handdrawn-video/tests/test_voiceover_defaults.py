from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
HELPER_PATH = ROOT / "scripts" / "postprocess_voiceover.py"
SPEC = importlib.util.spec_from_file_location("postprocess_voiceover", HELPER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {HELPER_PATH}")
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


class VoiceoverDefaultsTest(unittest.TestCase):
    def test_default_speed_filter_is_supported(self) -> None:
        self.assertEqual(HELPER.atempo_chain(1.2), "atempo=1.200000")

    def test_atempo_chain_handles_ffmpeg_limits(self) -> None:
        self.assertEqual(HELPER.atempo_chain(2.5), "atempo=2.000000,atempo=1.250000")
        self.assertEqual(HELPER.atempo_chain(0.25), "atempo=0.500000,atempo=0.500000")

    def test_caption_cleanup_is_not_subtitle_generation(self) -> None:
        self.assertEqual(HELPER.clean_caption("工具、。"), "工具。")
        self.assertEqual(HELPER.clean_caption("等……。"), "等……")

    def test_skill_contract_declares_no_subtitle_default(self) -> None:
        skill_text = (ROOT / "skill-package" / "story-to-handdrawn-video" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("--speed 1.2", skill_text)
        self.assertIn("--subtitle-mode none", skill_text)
        self.assertIn("does not burn or mux it", skill_text)


if __name__ == "__main__":
    unittest.main()
