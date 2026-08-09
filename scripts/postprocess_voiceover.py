#!/usr/bin/env python3
"""Create a synchronized voiceover video from a rendered storyboard.

The default delivery is a subtitle-free MP4.  A storyboard-timed narration is
generated scene by scene, then the video and audio are retimed together so the
default 1.2x playback speed cannot desynchronize them.  Subtitle files are
opt-in and are never muxed into the MP4.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def resolve_executable(value: str, label: str) -> str:
    candidate = Path(value).expanduser()
    if candidate.is_file():
        return str(candidate.resolve())

    names = [value]
    if os.name == "nt":
        names.extend([f"{value}.cmd", f"{value}.exe", f"{value}.ps1"])
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise SystemExit(
        f"Required {label} executable not found: {value}. "
        "Install it or pass the explicit executable path."
    )


def probe_duration(path: Path, ffprobe: str) -> float:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def atempo_chain(speed: float) -> str:
    if speed <= 0:
        raise ValueError("audio speed must be greater than zero")
    factors: list[float] = []
    remaining = speed
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    while remaining < 0.5:
        factors.append(0.5)
        remaining /= 0.5
    factors.append(remaining)
    return ",".join(f"atempo={factor:.6f}" for factor in factors)


def timestamp(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def clean_caption(value: object) -> str:
    return (
        str(value)
        .strip()
        .replace("，。", "。")
        .replace("、。", "。")
        .replace("……。", "……")
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synchronized voiceover; default output has no subtitle stream."
    )
    parser.add_argument("--storyboard", type=Path, required=True)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--output", type=Path, help="Final MP4; defaults to out/picture_voiceover.mp4")
    parser.add_argument("--audio-output", type=Path, help="Standalone M4A; defaults beside the MP4")
    parser.add_argument("--manifest-output", type=Path, help="Runtime manifest; defaults beside the MP4")
    parser.add_argument("--subtitle-output", type=Path, help="SRT path when --subtitle-mode srt is selected")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    parser.add_argument("--rate", default="-5%", help="Base Edge TTS rate before final playback speed")
    parser.add_argument(
        "--speed",
        type=float,
        default=1.2,
        help="Synchronized video/audio playback speed; default: 1.2",
    )
    parser.add_argument(
        "--subtitle-mode",
        choices=("none", "srt"),
        default="none",
        help="Default none; srt creates an external subtitle file and never muxes it",
    )
    parser.add_argument("--edge-tts", default="edge-tts")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.speed <= 0:
        raise SystemExit("--speed must be greater than zero")

    storyboard_path = args.storyboard.expanduser().resolve()
    video_path = args.video.expanduser().resolve()
    if not storyboard_path.is_file():
        raise SystemExit(f"Storyboard not found: {storyboard_path}")
    if not video_path.is_file():
        raise SystemExit(f"Video not found: {video_path}")

    edge_tts = resolve_executable(args.edge_tts, "Edge TTS")
    ffmpeg = resolve_executable(args.ffmpeg, "FFmpeg")
    ffprobe = resolve_executable(args.ffprobe, "FFprobe")

    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise SystemExit("Storyboard must contain a non-empty scenes array")

    default_dir = video_path.parent
    out_dir = (args.out_dir or default_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    output = (args.output or out_dir / "picture_voiceover.mp4").expanduser().resolve()
    audio_output = (
        args.audio_output or output.with_suffix(".m4a")
    ).expanduser().resolve()
    manifest_output = (
        args.manifest_output or output.with_suffix(".json")
    ).expanduser().resolve()
    subtitle_output = (
        args.subtitle_output or output.with_suffix(".srt")
    ).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    audio_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)

    segments_dir = out_dir / f"{output.stem}_segments"
    segments_dir.mkdir(parents=True, exist_ok=True)
    concat_list = segments_dir / "concat.txt"
    timed_wav = segments_dir / "timeline.wav"
    concat_lines: list[str] = []
    subtitles: list[str] = []
    scene_manifest: list[dict[str, object]] = []
    timeline = 0.0

    for scene in scenes:
        scene_id = str(scene.get("id", len(scene_manifest) + 1))
        target = float(scene.get("duration_sec", 0))
        if target <= 0:
            raise SystemExit(f"Scene {scene_id} has an invalid duration_sec: {target}")
        narration = str(scene.get("narration") or scene.get("text") or "").replace("\n", " ").strip()
        if not narration:
            raise SystemExit(f"Scene {scene_id} has no narration or text")

        text_path = segments_dir / f"{scene_id}.txt"
        raw_audio = segments_dir / f"{scene_id}_raw.mp3"
        timed_audio = segments_dir / f"{scene_id}_timed.wav"
        text_path.write_text(narration + "\n", encoding="utf-8")
        run(
            [
                edge_tts,
                "-f",
                str(text_path),
                "-v",
                args.voice,
                f"--rate={args.rate}",
                "--write-media",
                str(raw_audio),
            ]
        )

        raw_duration = probe_duration(raw_audio, ffprobe)
        filters: list[str] = []
        if raw_duration > target + 0.03:
            filters.append(atempo_chain(raw_duration / target))
        filters.extend(
            [
                f"apad=pad_dur={target:.3f}",
                f"atrim=duration={target:.3f}",
                "asetpts=N/SR/TB",
            ]
        )
        run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(raw_audio),
                "-af",
                ",".join(filters),
                "-ar",
                "48000",
                "-ac",
                "2",
                "-c:a",
                "pcm_s16le",
                str(timed_audio),
            ]
        )
        concat_lines.append(f"file '{timed_audio.as_posix()}'")

        caption = clean_caption(scene.get("text", narration))
        final_start = timeline / args.speed
        final_end = (timeline + target) / args.speed
        if args.subtitle_mode == "srt":
            subtitles.append(
                f"{len(subtitles) + 1}\n"
                f"{timestamp(final_start)} --> {timestamp(final_end)}\n"
                f"{caption}\n"
            )
        scene_manifest.append(
            {
                "id": scene_id,
                "target_duration_sec": target,
                "raw_duration_sec": raw_duration,
                "narration": narration,
            }
        )
        timeline += target

    concat_list.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
    run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c:a",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(timed_wav),
        ]
    )

    # Encode the speed-adjusted standalone audio first. The same file is then
    # mapped into the MP4, so the two delivered tracks share one time base.
    run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(timed_wav),
            "-af",
            atempo_chain(args.speed),
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(audio_output),
        ]
    )

    # Explicit video/audio mapping prevents any subtitle or data stream from
    # being inherited from the input container. The subtitle file, if opted
    # into, remains an external artifact and is never muxed into the MP4.
    run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_output),
            "-filter_complex",
            f"[0:v]setpts=PTS/{args.speed:.6f}[v]",
            "-map",
            "[v]",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )

    subtitle_path: str | None = None
    if args.subtitle_mode == "srt":
        subtitle_output.write_text("\n".join(subtitles), encoding="utf-8")
        subtitle_path = subtitle_output.name

    manifest_output.write_text(
        json.dumps(
            {
                "video_input": video_path.name,
                "video_output": output.name,
                "audio_output": audio_output.name,
                "voice": args.voice,
                "rate": args.rate,
                "speed": args.speed,
                "subtitle_mode": args.subtitle_mode,
                "subtitle_output": subtitle_path,
                "original_timeline_duration_sec": timeline,
                "final_duration_sec": probe_duration(output, ffprobe),
                "scenes": scene_manifest,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "video": str(output),
                "audio": str(audio_output),
                "manifest": str(manifest_output),
                "subtitle_mode": args.subtitle_mode,
                "speed": args.speed,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
