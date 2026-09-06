import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .. import ai

router = APIRouter(prefix="/chat", tags=["ai"])

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES = 10


@router.post("")
async def chat(
    message: str = Form(""),
    history: str = Form("[]"),
    files: list[UploadFile] = File(default=[]),
):
    """One AI turn. History is a JSON list of {role, content} from previous turns."""
    try:
        past = json.loads(history)
    except json.JSONDecodeError:
        raise HTTPException(400, "history must be valid JSON")
    if not isinstance(past, list):
        raise HTTPException(400, "history must be a JSON list")
    turns = [
        ai.Message(role=m["role"], content=m["content"])
        for m in past
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")
    ]

    if len(files) > MAX_FILES:
        raise HTTPException(400, f"At most {MAX_FILES} files per message")

    attachments = []
    for upload in files:
        data = await upload.read()
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(400, f"{upload.filename} exceeds the 10 MB limit")
        try:
            attachments.append(
                ai.parse_upload(upload.filename or "file", upload.content_type or "", data)
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))

    if not message.strip() and not attachments:
        raise HTTPException(400, "Send a message or a file")

    return {"reply": ai.run_chat(turns, message, attachments), "provider": ai.provider_name()}
