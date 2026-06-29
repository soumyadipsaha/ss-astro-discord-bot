import json
import os

os.environ.setdefault("DISCORD_PUBLIC_KEY", "")
os.environ.setdefault("DISCORD_TOKEN", "")
os.environ.setdefault("DISCORD_APP_ID", "")

from nacl.signing import SigningKey
from starlette.testclient import TestClient

from app.main import app


def _sign(sk: SigningKey, payload: dict):
    body = json.dumps(payload).encode()
    ts = "1700000000"
    sig = sk.sign(ts.encode() + body).signature.hex()
    return {
        "X-Signature-Ed25519": sig,
        "X-Signature-Timestamp": ts,
        "Content-Type": "application/json",
    }, body


def setup_module(_module):
    sk = SigningKey.generate()
    setup_module._sk = sk
    os.environ["DISCORD_PUBLIC_KEY"] = sk.verify_key.encode().hex()


def test_ping_acknowledged():
    headers, body = _sign(setup_module._sk, {"type": 1})
    with TestClient(app) as c:
        r = c.post("/interactions", content=body, headers=headers)
    assert r.status_code == 200
    assert r.json() == {"type": 1}


def test_vedic_command_returns_embed():
    payload = {
        "type": 2,
        "data": {
            "name": "vedic",
            "options": [
                {"name": "date", "value": "2000-01-01"},
                {"name": "time", "value": "12:00"},
                {"name": "lat", "value": 28.6139},
                {"name": "lon", "value": 77.2090},
                {"name": "tz", "value": 5.5},
                {"name": "chalit", "value": True},
            ],
        },
    }
    headers, body = _sign(setup_module._sk, payload)
    with TestClient(app) as c:
        r = c.post("/interactions", content=body, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == 4
    embed = data["data"]["embeds"][0]
    assert "Sidereal" in embed["title"]
    assert any("Lagna" in f["name"] for f in embed["fields"])
    assert any("Navagraha" in f["name"] for f in embed["fields"])


def test_invalid_signature_rejected():
    headers, body = _sign(setup_module._sk, {"type": 1})
    headers["X-Signature-Ed25519"] = "00" * 64
    with TestClient(app) as c:
        r = c.post("/interactions", content=body, headers=headers)
    assert r.status_code == 401


def test_health_and_cron():
    with TestClient(app) as c:
        assert c.get("/health").json() == {"ok": True}
        assert c.get("/cron").json() == {"ok": True}
