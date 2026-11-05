import asyncio
import uuid
import urllib.parse
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="Local LLM Chat Service")

# Setup Jinja2 templates directory
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    """Render the main chat interface."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/chat", response_class=HTMLResponse)
async def post_chat(request: Request, prompt: str = Form(...)):
    """
    Handle the user submitting a message.
    Returns HTML containing the user's message and a placeholder for the AI response
    that connects to the SSE streaming endpoint.
    """
    prompt_encoded = urllib.parse.quote(prompt)
    msg_id = f"msg-{uuid.uuid4().hex}"
    
    # HTML response to inject into the chat container
    html_content = f"""
    <div class="message user">{prompt}</div>
    <div class="message ai" id="{msg_id}" hx-ext="sse" sse-connect="/stream?prompt={prompt_encoded}&msg_id={msg_id}">
        <span sse-swap="message" hx-swap="beforeend"></span>
    </div>
    """
    return HTMLResponse(content=html_content)

async def mock_llm_generator(prompt: str, msg_id: str):
    """
    Simulates a local LLM generating a response word by word.
    Yields SSE events that HTMX will inject into the DOM.
    """
    # Simulate processing delay
    await asyncio.sleep(0.5)
    
    words = f"Here is a simulated response to your prompt: '{prompt}'. This output is streamed word by word using Server-Sent Events, mimicking tools like OpenWebUI without needing their full stack.".split()
    
    accumulated_text = ""
    for word in words:
        await asyncio.sleep(0.1) # Simulate token generation delay
        accumulated_text += word + " "
        # HTMX will append this word to the target container
        yield {
            "event": "message",
            "data": f"{word} "
        }
    
    # Send an out-of-band swap to replace the entire SSE container
    # This removes the hx-ext="sse" element and stops the SSE connection gracefully
    final_html = f'<div id="{msg_id}" hx-swap-oob="true" class="message ai">{accumulated_text.strip()}</div>'
    yield {
        "event": "message",
        "data": final_html
    }

@app.get("/stream")
async def stream_response(request: Request, prompt: str, msg_id: str):
    """
    Endpoint for SSE streaming. HTMX connects here to stream the LLM response.
    """
    return EventSourceResponse(mock_llm_generator(prompt, msg_id))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
