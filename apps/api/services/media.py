from __future__ import annotations

import hashlib
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import Asset, ContentVariant


class StorageProvider(ABC):
    @abstractmethod
    def public_uri(self, path: Path) -> str:
        raise NotImplementedError


class LocalStorageProvider(StorageProvider):
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def public_uri(self, path: Path) -> str:
        resolved = path.resolve()
        if self.root not in resolved.parents:
            raise ValueError("Media path escaped configured storage root")
        return f"/media/{resolved.relative_to(self.root)}"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def _wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_pin(db: Session, variant: ContentVariant, settings: Settings) -> str:
    storage = LocalStorageProvider(settings.media_root)
    product = variant.idea.deal.product
    templates = __import__("apps.api.services.content", fromlist=["load_templates"]).load_templates()
    accent = templates.get(variant.template_key, templates["deal_alert"])["accent"]
    image = Image.new("RGB", (1000, 1500), "#08111F")
    draw = ImageDraw.Draw(image)
    for y in range(1500):
        ratio = y / 1500
        draw.line((0, y, 1000, y), fill=(8 + int(12 * ratio), 17 + int(18 * ratio), 31 + int(28 * ratio)))
    draw.rounded_rectangle((70, 70, 930, 1430), radius=48, fill="#101C2E", outline=accent, width=5)
    draw.rounded_rectangle((105, 105, 430, 165), radius=28, fill=accent)
    draw.text((135, 118), "CURRENT DEAL", font=_font(28, True), fill="#08111F")
    title_font = _font(70, True)
    y = 230
    for line in _wrapped(draw, product.product_name, title_font, 760)[:4]:
        draw.text((120, y), line, font=title_font, fill="#F8FAFC")
        y += 84
    draw.rounded_rectangle((120, 610, 880, 1010), radius=42, fill="#0B1424")
    draw.ellipse((350, 690, 650, 990), fill=accent)
    draw.rounded_rectangle((440, 740, 560, 950), radius=25, fill="#E2E8F0")
    draw.line((500, 950, 430, 1000), fill="#E2E8F0", width=24)
    draw.line((500, 950, 570, 1000), fill="#E2E8F0", width=24)
    price = f"${product.current_price}"
    draw.text((120, 1070), price, font=_font(92, True), fill=accent)
    draw.text((125, 1185), f"Listed discount {product.discount_percent}%", font=_font(34), fill="#CBD5E1")
    draw.text((125, 1270), "Check current price & availability →", font=_font(33, True), fill="#F8FAFC")
    draw.text((125, 1360), "Affiliate link", font=_font(23), fill="#94A3B8")
    output = storage.root / f"{variant.id}.png"
    image.save(output, format="PNG", optimize=True)
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    db.add(
        Asset(
            product_id=product.id,
            asset_type="generated_pin",
            uri=storage.public_uri(output),
            source="DealForge original template renderer",
            license="Original generated composition",
            authorization="Generated from supplied product facts; no third-party media embedded",
            checksum=checksum,
        )
    )
    variant.media_uri = storage.public_uri(output)
    db.commit()
    return variant.media_uri


def render_video(db: Session, variant: ContentVariant, settings: Settings) -> str | None:
    if not variant.media_uri:
        render_pin(db, variant, settings)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return None
    root = settings.media_root.resolve()
    image_path = root / Path(variant.media_uri or "").name
    output = root / f"{variant.id}.mp4"
    command = [
        ffmpeg,
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-vf",
        "scale=1080:1620,crop=1080:1920:y='max(0,min(150,75+35*sin(t/3)))',fade=t=in:st=0:d=0.4,fade=t=out:st=24.3:d=0.7",
        "-t",
        "25",
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    subprocess.run(command, check=True, timeout=90, capture_output=True)  # noqa: S603
    return LocalStorageProvider(settings.media_root).public_uri(output)
