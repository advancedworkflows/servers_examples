from fastapi.testclient import TestClient
from src.main import app
import pytest

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "Local LLM Chat" in response.text

def test_post_chat():
    response = client.post("/chat", data={"prompt": "Hello world"})
    assert response.status_code == 200
    assert "Hello world" in response.text
    assert "sse-connect" in response.text
    assert "hx-ext=\"sse\"" in response.text

@pytest.mark.asyncio
async def test_stream_endpoint():
    # Since we use EventSourceResponse, we can use the test client to get the stream
    with client.stream("GET", "/stream?prompt=Test&msg_id=123") as response:
        assert response.status_code == 200
        content = response.iter_lines()
        first_event = next(content)
        assert first_event.startswith("event: message")
