from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import StoryProject


def _ffmpeg_executable() -> str:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        import imageio_ffmpeg
    except ImportError as exc:  # pragma: no cover - exercised by deployment checks
        raise RuntimeError("FFmpeg is unavailable. Install imageio-ffmpeg or provide ffmpeg on PATH.") from exc
    return str(imageio_ffmpeg.get_ffmpeg_exe())


def _probe_duration(ffmpeg: str, media_path: Path) -> float:
    result = subprocess.run(  # noqa: S603
        [ffmpeg, "-hide_banner", "-i", str(media_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"Could not determine duration for {media_path.name}.")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{millis:03d}"


def _subtitle_chunks(script: str, max_words: int = 9) -> list[str]:
    chunks: list[str] = []
    sentences = re.split(r"(?<=[.!?])\s+", script.strip())
    for sentence in sentences:
        words = sentence.split()
        sentence_chunks = [words[index : index + max_words] for index in range(0, len(words), max_words)]
        if len(sentence_chunks) > 1 and len(sentence_chunks[-1]) < 3:
            orphan = sentence_chunks.pop()
            sentence_chunks[-1].extend(orphan)
        chunks.extend(" ".join(chunk) for chunk in sentence_chunks)
    return chunks


def _write_subtitles(script: str, duration: float, output: Path) -> None:
    chunks = _subtitle_chunks(script)
    total_words = sum(len(chunk.split()) for chunk in chunks)
    elapsed = 0.0
    rows: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        share = len(chunk.split()) / total_words
        end = duration if index == len(chunks) else min(duration, elapsed + duration * share)
        rows.extend([str(index), f"{_timestamp(elapsed)} --> {_timestamp(end)}", chunk, ""])
        elapsed = end
    output.write_text("\n".join(rows), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def render_story_video(db: Session, project: StoryProject, settings: Settings) -> str:
    if project.approved_at is None:
        raise ValueError("Human approval is required before video rendering.")
    report = project.quality_report or {}
    if not report.get("passed"):
        raise ValueError("The factual and safety validation gates must pass before rendering.")

    ffmpeg = _ffmpeg_executable()
    say = shutil.which("say")
    if say is None:
        raise RuntimeError("The configured local narration provider is unavailable.")

    output_dir = Path(settings.media_root) / "case-lantern" / project.slug
    visual_dir = output_dir / "visuals"
    output_dir.mkdir(parents=True, exist_ok=True)
    visuals = sorted(visual_dir.glob("*.png"))
    if len(visuals) < 3:
        raise RuntimeError(f"At least three original PNG visuals are required; found {len(visuals)}.")

    narration = output_dir / "narration.aiff"
    subtitles = output_dir / "captions.srt"
    video = output_dir / "case-lantern-v1.mp4"
    subprocess.run(  # noqa: S603
        [say, "-v", "Samantha", "-r", "175", "-o", str(narration), project.script],
        check=True,
        capture_output=True,
        timeout=120,
    )
    narration_duration = _probe_duration(ffmpeg, narration)
    _write_subtitles(project.script, narration_duration, subtitles)

    segment_duration = math.ceil(narration_duration / len(visuals)) + 1
    frames = segment_duration * 30
    command: list[str] = [ffmpeg, "-y"]
    for visual in visuals:
        command.extend(["-loop", "1", "-t", str(segment_duration), "-i", str(visual)])
    command.extend(["-i", str(narration)])

    filters: list[str] = []
    for index in range(len(visuals)):
        pan_x = "iw/2-(iw/zoom/2)" if index % 2 == 0 else "iw-iw/zoom"
        filters.append(
            f"[{index}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,zoompan=z='min(zoom+0.00018,1.055)':x='{pan_x}':"
            f"y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30,setsar=1[v{index}]"
        )
    concat_inputs = "".join(f"[v{index}]" for index in range(len(visuals)))
    filters.append(f"{concat_inputs}concat=n={len(visuals)}:v=1:a=0[base]")
    subtitle_path = str(subtitles).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    filters.append(
        "[base]drawtext=text='CASE LANTERN':fontcolor=0xD3A35B:fontsize=38:"
        "font='Arial Bold':x=64:y=82:shadowcolor=black@0.75:shadowx=2:shadowy=2,"
        "drawtext=text='AI-ASSISTED ILLUSTRATION • SOURCED HISTORY':fontcolor=white@0.8:fontsize=22:"
        "font='Arial':x=64:y=132:shadowcolor=black@0.7:shadowx=2:shadowy=2:enable='between(t,0,5)',"
        f"subtitles='{subtitle_path}':force_style='FontName=Arial,FontSize=11,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&HCC000000,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=125'[video]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[video]",
            "-map",
            f"{len(visuals)}:a",
            "-t",
            f"{narration_duration:.3f}",
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-profile:v",
            "high",
            "-level",
            "4.1",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(video),
        ]
    )
    subprocess.run(command, check=True, capture_output=True, timeout=300)  # noqa: S603
    if not video.exists() or video.stat().st_size < 500_000:
        raise RuntimeError("Rendered video failed the minimum file-size validation gate.")
    rendered_duration = _probe_duration(ffmpeg, video)
    if abs(rendered_duration - narration_duration) > 1.5:
        raise RuntimeError("Rendered video duration does not match its narration.")

    manifest: dict[str, Any] = {
        "schema_version": "case-lantern-render-v1",
        "story_id": project.id,
        "title": project.title,
        "video": video.name,
        "video_sha256": _sha256(video),
        "duration_seconds": round(rendered_duration, 3),
        "resolution": "1080x1920",
        "video_codec": "H.264",
        "audio_codec": "AAC",
        "visuals": [{"file": path.name, "sha256": _sha256(path)} for path in visuals],
        "narration": {"provider": "macOS system voice", "voice": "Samantha", "cloned_voice": False},
        "disclosure": {
            "ai_assisted_visuals": True,
            "creator_ai_label_required": True,
            "caption_text": "AI-assisted original illustrations and narration.",
        },
        "rights": "Original generated illustrations; no third-party clips embedded.",
        "human_approval_required_for_publication": True,
    }
    (output_dir / "render-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    project.media_uri = str(video)
    project.duration_seconds = round(rendered_duration)
    project.status = "video_ready"
    project.quality_report = {
        **report,
        "render": {
            "passed": True,
            "duration_seconds": round(rendered_duration, 3),
            "resolution": "1080x1920",
            "video_sha256": manifest["video_sha256"],
            "visual_count": len(visuals),
            "copyrighted_clips_used": False,
            "cloned_voice_used": False,
            "ai_label_required": True,
        },
    }
    db.commit()
    return str(video)
