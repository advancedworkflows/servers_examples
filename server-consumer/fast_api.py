from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

DATA = {
    "message": "Hello from FastAPI",
    "status": "success",
    "items": [
        {"id": 1, "name": "Apple"},
        {"id": 2, "name": "Orange"},
        {"id": 3, "name": "Banana"},
    ],
}

HTML = """
<!DOCTYPE html>
<html lang="en">
<body style="font-family: Georgia, serif;">
    <h1 style="color: red;">HELLO</h1>
    <p style="color: blue; font-style: italic;">world</p>
</body>
</html>
"""


@app.get("/data")
def get_data() -> dict:
    return DATA


@app.get("/html", response_class=HTMLResponse)
def get_html() -> str:
    return HTML


@app.get("/status")
def get_status() -> dict:
    return {
        "running": True,
    }


# 1a. Add path parameter, Let say we want to display Hello with name provided in browser filed
# 1b. Investigate query parameters
# 1c. Use pydantic for json request bodies (create object wth BaseModel and use it in path func signature)
# 1d. Use Response Model with pydantic (the same BaseModel) -> `@app.get("/items/{item_id}", response_model=ItemPublic)`

# 2 Add POST method, understand what it does. have minimal def with similar return one get, one post

# 3. Work with HTML, CSS

# ASYNC
# Use def when calling blocking libraries such as normal file I/O, many database clients, or urllib.
# Use async def when calling async libraries with await, such as httpx.AsyncClient, async database clients, or async Redis clients.
# Understand blocking, for example urlopen to nonexistening server

# MIDDLEWARE
# Debug its running around every request. 
# request
#   -> middleware before
#     -> route function
#   -> middleware after
# response

# TOUCH ON OPENAPI AND SWAGGER
# http://127.0.0.1:8000/docs
# http://127.0.0.1:8000/redoc
# http://127.0.0.1:8000/openapi.json

# TESTING
# from fastapi.testclient import TestClient
# from fast_api import app
# client = TestClient(app)

# CORS
# for browser to server
