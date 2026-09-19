import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from src.main import app
import os
import sys

# Ensure pytest can find src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Load all scenarios from the feature file
scenarios('../features/chat.feature')

@pytest.fixture
def client():
    return TestClient(app)

@given('the chat interface is running')
def chat_running():
    # The test client acts as our running application, nothing to do here
    pass

@when('the user navigates to the root URL')
def navigate_root(client, request):
    response = client.get("/")
    request.response = response

@then('the user should see the chat UI')
def verify_chat_ui(request):
    assert request.response.status_code == 200
    assert "Local LLM Chat" in request.response.text

@when(parsers.parse('the user submits a message "{message}"'))
def submit_message(client, request, message):
    response = client.post("/chat", data={"prompt": message})
    request.response = response

@then(parsers.parse('the response should contain the user message "{message}"'))
def verify_user_message(request, message):
    assert request.response.status_code == 200
    assert message in request.response.text

@then('the response should include an SSE connection setup')
def verify_sse_setup(request):
    assert "sse-connect" in request.response.text
    assert "hx-ext=\"sse\"" in request.response.text
