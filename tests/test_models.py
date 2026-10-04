import json

import httpx
import pytest
from pydantic import ValidationError

from study.config import Settings
from study.models import ModelError, Models, StructuredOutputError
from study.schemas import Verdict


def gateway(settings=None, *, cloud=False, malformed=False):
    models = Models(settings or Settings(_env_file=None))
    requests = []

    def respond(request):
        payload = json.loads(request.content)
        requests.append((request.url.path, payload))
        if request.url.path == "/api/show":
            family = "gemma3" if "gemma" in payload["model"] else "qwen2"
            return httpx.Response(200, json={"model_info": {"general.architecture": family},
                                            **({"remote_model": "cloud"} if cloud else {})})
        return httpx.Response(200, json={"message": {"content": "oops" if malformed else
                                            '{"supported":true,"reason":"grounded"}'}})

    models.client.close()
    models.client = httpx.Client(base_url="http://127.0.0.1:11434", transport=httpx.MockTransport(respond))
    return models, requests


def test_structured_gateway_never_streams_and_has_one_call():
    models, requests = gateway()
    try:
        assert models.structured("verifier", Verdict, "Check support", {"claim": "x"}).supported
        chats = [body for path, body in requests if path == "/api/chat"]
        assert len(chats) == 1 and chats[0]["stream"] is False and chats[0]["keep_alive"] == 0
        assert chats[0]["format"] == Verdict.model_json_schema()
    finally:
        models.close()


def test_invalid_schema_has_no_hidden_retry():
    models, requests = gateway(malformed=True)
    try:
        with pytest.raises(StructuredOutputError):
            models.structured("generator", Verdict, "Check", {})
        assert sum(path == "/api/chat" for path, _ in requests) == 1
    finally:
        models.close()


def test_family_metadata_and_cloud_fail_closed():
    models, _ = gateway(Settings(_env_file=None, verifier_model="gemma3:1b"))
    try:
        with pytest.raises(ModelError, match="different model family"):
            models.structured("verifier", Verdict, "Check", {})
    finally:
        models.close()
    models, _ = gateway(cloud=True)
    try:
        assert not models.health()["ready"]
    finally:
        models.close()


@pytest.mark.parametrize("kwargs", [{"ollama_url": "https://cloud.example"},
                                   {"ollama_url": "http://127.0.0.1:11434/redirect"},
                                   {"generator_model": "model:cloud"}])
def test_remote_endpoints_and_cloud_tags_rejected(kwargs):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **kwargs)
