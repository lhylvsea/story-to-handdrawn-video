#!/usr/bin/env python3
"""Convenience entry point for the story-to-handdrawn-video Remotion project."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


def default_project() -> Path:
    """Find the project without relying on the original author's machine path."""
    configured = os.environ.get("STORY_VIDEO_PROJECT")
    if configured:
        return Path(configured).expanduser().resolve()

    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "package.json").exists() and (
            candidate / "scripts/story-to-video.mjs"
        ).exists():
            return candidate
    return Path.cwd()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan, generate, import, or render a hand-drawn story animation."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", type=Path, help="UTF-8 story text file")
    source.add_argument("--text", help="Inline story copy")
    source.add_argument(
        "--images",
        type=Path,
        nargs="+",
        help="Uploaded comic pages or full-frame images, in playback order",
    )
    parser.add_argument("--title", default="手绘故事")
    parser.add_argument(
        "--style",
        default="colored-pencil-diary",
        help="Built-in style id, number, Chinese name, or alias",
    )
    parser.add_argument(
        "--list-styles",
        action="store_true",
        help="Print the built-in style catalog and exit",
    )
    parser.add_argument("--character-lock")
    parser.add_argument("--visual-plan", type=Path)
    parser.add_argument(
        "--source",
        type=Path,
        help="Raw source text file for article-content review mode",
    )
    parser.add_argument(
        "--review-dir",
        type=Path,
        default=Path("review"),
        help="Directory for the review report, diff, and manifest",
    )
    parser.add_argument(
        "--review-manifest",
        type=Path,
        help="Pending review manifest used by approve mode",
    )
    parser.add_argument(
        "--approved-review",
        type=Path,
        help="Approval record to validate before generation",
    )
    parser.add_argument(
        "--mode",
        choices=("plan", "review", "approve", "generate", "full", "import", "render", "preview"),
        default="plan",
    )
    parser.add_argument("--generator", choices=("codex", "api"), default="codex")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--text-mode", choices=("image2", "font"), default="font")
    parser.add_argument("--transition", choices=("cut", "page-flip"), default="cut")
    parser.add_argument("--transition-sec", type=float, default=0.7)
    parser.add_argument("--page-duration", type=float, default=4.4)
    parser.add_argument("--layout", choices=("auto", "composite", "full"), default="auto")
    parser.add_argument(
        "--split-y",
        action="append",
        default=[],
        metavar="SCENE:PIXELS",
        help="Override the caption/art split for an uploaded scene (repeatable)",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=default_project(),
    )
    return parser.parse_args()


def require_project(project: Path) -> None:
    required = (project / "package.json", project / "scripts/story-to-video.mjs")
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Story video project is incomplete; missing: {', '.join(missing)}")


def run(command: list[str], project: Path) -> None:
    subprocess.run(command, cwd=project, check=True)


NPM = "npm.cmd" if os.name == "nt" else "npm"
NODE = "node.exe" if os.name == "nt" else "node"


def resolve_project_path(path: Path, project: Path) -> Path:
    if path.is_absolute():
        return path.expanduser().resolve()
    return (project / path).expanduser().resolve()


def main() -> None:
    args = parse_args()
    project = args.project_dir.expanduser().resolve()
    require_project(project)

    if args.list_styles:
        run([NPM, "run", "styles"], project)
        return

    if args.mode == "review":
        if args.images or not args.input or not args.source:
            raise SystemExit("--mode review requires --source and --input draft text files")
        run(
            [
                NODE,
                "scripts/review-story.mjs",
                "--mode",
                "create",
                "--source",
                str(resolve_project_path(args.source, project)),
                "--draft",
                str(resolve_project_path(args.input, project)),
                "--output",
                str(resolve_project_path(args.review_dir, project)),
            ],
            project,
        )
        return

    if args.mode == "approve":
        if args.images or not args.input or not args.review_manifest:
            raise SystemExit("--mode approve requires --input and --review-manifest")
        run(
            [
                NODE,
                "scripts/review-story.mjs",
                "--mode",
                "approve",
                "--manifest",
                str(resolve_project_path(args.review_manifest, project)),
                "--draft",
                str(resolve_project_path(args.input, project)),
            ],
            project,
        )
        return

    if args.images:
        if args.mode == "import":
            raise SystemExit("--mode import is reserved for Codex Image2 manifests")
        command = [NPM, "run", "import:uploaded", "--"]
        for image in args.images:
            command += ["--image", str(image.expanduser().resolve())]
        command += [
            "--title",
            args.title,
            "--transition",
            args.transition,
            "--transition-sec",
            str(args.transition_sec),
            "--page-duration",
            str(args.page_duration),
            "--layout",
            args.layout,
        ]
        for split_y in args.split_y:
            command += ["--split-y", split_y]
        run(command, project)
        if args.mode in {"full", "render"}:
            run([NPM, "run", "render:uploaded"], project)
            print(f"Rendered uploaded-image video: {project / 'out/uploaded_picture_silent.mp4'}")
        elif args.mode == "preview":
            run([NPM, "run", "render:uploaded:preview"], project)
            print(
                f"Rendered uploaded-image preview: "
                f"{project / 'out/uploaded_picture_silent-preview.mp4'}"
            )
        else:
            print(f"Prepared uploaded-image storyboard: {project / 'storyboard.uploaded.json'}")
        return

    if args.mode in {"render", "preview"}:
        run([NPM, "run", "render" if args.mode == "render" else "render:preview"], project)
        output = project / "out" / (
            "picture_silent.mp4" if args.mode == "render" else "picture_silent-preview.mp4"
        )
        print(f"Rendered silent video: {output}")
        return

    if args.mode == "import":
        command = [NPM, "run", "import:codex", "--", "--apply"]
        if args.manifest:
            command += ["--manifest", str(args.manifest.expanduser().resolve())]
        run(command, project)
        print(f"Imported Codex Image2 assets and activated: {project / 'storyboard.json'}")
        return

    if not args.input and not args.text:
        raise SystemExit(
            "--input, --text, or --images is required for plan, generate, and full modes"
        )
    if (
        args.generator == "api"
        and args.mode in {"generate", "full"}
        and not os.environ.get("OPENAI_API_KEY")
    ):
        raise SystemExit("OPENAI_API_KEY is required only for --generator api")

    if args.approved_review:
        if not args.input or args.mode not in {"generate", "full"}:
            raise SystemExit("--approved-review requires --input and --mode generate or full")
        run(
            [
                NODE,
                "scripts/review-story.mjs",
                "--mode",
                "check",
                "--approval",
                str(resolve_project_path(args.approved_review, project)),
                "--draft",
                str(resolve_project_path(args.input, project)),
            ],
            project,
        )

    command = [NPM, "run", "story", "--"]
    if args.input:
        command += ["--input", str(args.input.expanduser().resolve())]
    else:
        command += ["--text", args.text]
    command += [
        "--title",
        args.title,
        "--style",
        args.style,
        "--text-mode",
        args.text_mode,
        "--generator",
        args.generator,
        "--transition",
        args.transition,
        "--transition-sec",
        str(args.transition_sec),
    ]
    if args.character_lock:
        command += ["--character-lock", args.character_lock]
    if args.visual_plan:
        command += ["--visual-plan", str(args.visual_plan.expanduser().resolve())]
    if args.manifest:
        command += ["--manifest", str(args.manifest.expanduser().resolve())]

    if args.mode in {"generate", "full"}:
        command.append("--generate")
        if args.generator == "api":
            command.append("--apply")
    if args.mode == "full" and args.generator == "api":
        command.append("--render")
    if args.force:
        command.append("--force")

    run(command, project)
    if args.mode == "plan":
        print(f"Prepared dynamic storyboard plan: {project / 'storyboard.generated.json'}")
    elif args.generator == "codex":
        print(
            "Prepared Codex Image2 jobs without an API key. "
            "Codex should generate each job in codex-image-jobs.json, copy the masters to their "
            "output_master paths, then run --mode import (and --mode render for the final video)."
        )
    elif args.mode == "generate":
        print(f"Generated and activated storyboard: {project / 'storyboard.json'}")
    else:
        print(f"Rendered silent video: {project / 'out/picture_silent.mp4'}")


if __name__ == "__main__":
    main()
