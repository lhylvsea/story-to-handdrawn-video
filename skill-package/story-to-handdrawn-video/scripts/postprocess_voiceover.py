#!/usr/bin/env python3
"""Run the renderer project's reusable voiceover postprocessor.

The skill package is installed separately from the renderer repository. Set
STORY_VIDEO_PROJECT to the checkout that contains scripts/postprocess_voiceover.py
before invoking this adapter.
"""

from __future__ import annotations

import os
import runpy
from pathlib import Path

SCRIPT_INTERFACE = "internal-module"


def main() -> None:
    configured = os.environ.get("STORY_VIDEO_PROJECT")
    if not configured:
        raise SystemExit(
            "STORY_VIDEO_PROJECT must point to the any-to-handdrawn-video renderer checkout"
        )
    target = Path(configured).expanduser().resolve() / "scripts" / "postprocess_voiceover.py"
    if not target.is_file():
        raise SystemExit(f"Renderer voiceover helper not found: {target}")
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
