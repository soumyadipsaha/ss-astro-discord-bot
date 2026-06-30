import json
import logging

import httpx

log = logging.getLogger("vedic_bot")

API_BASE = "https://discord.com/api/v10"
EPHEMERAL = 1 << 6
TIMEOUT = 30.0


def _original_url(app_id: str, token: str) -> str:
    return f"{API_BASE}/webhooks/{app_id}/{token}/messages/@original"


async def edit_original_text(
    app_id: str, token: str, content: str, *, ephemeral: bool = False
) -> httpx.Response:
    """Replace the deferred "thinking" message with plain text content."""
    payload = {"content": content}
    if ephemeral:
        payload["flags"] = EPHEMERAL
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        return await client.patch(
            _original_url(app_id, token),
            data={"payload_json": json.dumps(payload)},
        )


async def edit_original_with_file(
    app_id: str,
    token: str,
    embed: dict,
    filename: str,
    data: bytes,
    content: str | None = None,
) -> httpx.Response:
    """Replace the deferred message with an embed that shows an inline attachment.

    The embed's image url MUST be ``attachment://<filename>`` so Discord links the
    embed image to the uploaded file.
    """
    payload: dict = {"embeds": [embed]}
    if content:
        payload["content"] = content
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        return await client.patch(
            _original_url(app_id, token),
            data={"payload_json": json.dumps(payload)},
            files={"files[0]": (filename, data, "image/png")},
        )
