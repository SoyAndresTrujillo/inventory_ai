"""Provider-neutral pieces: the port every adapter implements, and file parsing."""

import csv
import io
from dataclasses import dataclass
from typing import Literal, Protocol

import openpyxl

MAX_TEXT_CHARS = 400_000
MAX_ITERATIONS = 40

IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}


class AIError(Exception):
    """Anything that stops a turn: no credentials, provider down, unsupported input."""


@dataclass(frozen=True)
class Attachment:
    """One upload, already reduced to something a model can read."""

    kind: Literal["text", "image", "pdf"]
    filename: str
    media_type: str = ""
    text: str = ""
    data: bytes = b""


@dataclass(frozen=True)
class Message:
    role: Literal["user", "assistant"]
    content: str


class Provider(Protocol):
    """The port. Adapters translate this into whatever their SDK expects."""

    name: str
    model: str
    supports_images: bool

    def run(self, history: list[Message], message: str, attachments: list[Attachment]) -> str:
        """Run one turn, executing tools until the model is done. Returns the reply text."""


def parse_upload(filename: str, content_type: str, data: bytes) -> Attachment:
    """Turn one uploaded file into a neutral attachment. Never truncates silently."""
    if content_type in IMAGE_TYPES:
        return Attachment("image", filename, media_type=content_type, data=data)

    if content_type == "application/pdf":
        return Attachment("pdf", filename, media_type=content_type, data=data)

    if filename.lower().endswith((".xlsx", ".xlsm")):
        text = _excel_to_csv(data)
    else:
        text = data.decode("utf-8", errors="replace")

    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"{filename} is too large ({len(text)} characters). "
            "Split it into smaller files instead - truncating would drop products."
        )
    return Attachment("text", filename, text=text)


def _excel_to_csv(data: bytes) -> str:
    workbook = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out = io.StringIO()
    writer = csv.writer(out)
    for sheet in workbook.worksheets:
        out.write(f"# sheet: {sheet.title}\n")
        for row in sheet.iter_rows(values_only=True):
            if any(cell is not None for cell in row):
                writer.writerow(["" if cell is None else cell for cell in row])
    workbook.close()
    return out.getvalue()


def check_supported(provider: Provider, attachments: list[Attachment]) -> None:
    """Fail loudly on input this provider cannot read, instead of dropping it."""
    if not provider.supports_images:
        blocked = [a.filename for a in attachments if a.kind in ("image", "pdf")]
        if blocked:
            raise AIError(
                f"{provider.name} ({provider.model}) cannot read images or PDFs: "
                f"{', '.join(blocked)}. Send the data as text, CSV, Excel, XML or JSON, "
                "or switch AI_PROVIDER to a vision-capable model."
            )
