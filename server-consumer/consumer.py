import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response

# Server-to-server target: consumer.py calls fast_api.py from Python.
# Browser JavaScript must not call this URL directly because
# browser localhost means the user's machine, not this server process.
# This assumes both apps run in the same workspace/network namespace.
# If fast_api.py runs in another workspace, this localhost URL is wrong.
API_BASE_URL = "http://127.0.0.1:8000"

# Default editable endpoint shown in the browser.
DEFAULT_ENDPOINT = "data"

app = FastAPI()


def create_html_page() -> str:
    # json.dumps safely creates JavaScript string literals.
    default_endpoint_js = json.dumps(DEFAULT_ENDPOINT)

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>JSON Consumer</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
        }}

        .url-row {{
            display: flex;
            align-items: center;
            margin-bottom: 16px;
        }}

        .base-url {{
            padding: 10px;
            background: #eeeeee;
            border: 1px solid #cccccc;
            border-right: none;
            border-radius: 6px 0 0 6px;
            white-space: nowrap;
        }}

        #endpoint {{
            flex: 1;
            min-width: 200px;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #cccccc;
            border-radius: 0 6px 6px 0;
        }}

        button {{
            padding: 10px 18px;
            font-size: 16px;
            cursor: pointer;
        }}

        #requested-url {{
            margin-top: 16px;
            color: #555555;
        }}

        pre {{
            margin-top: 16px;
            padding: 16px;
            background: #f4f4f4;
            border: 1px solid #cccccc;
            border-radius: 6px;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }}

        .error {{
            color: darkred;
        }}
    </style>
</head>

<body>
    <h1>JSON Consumer</h1>

    <div class="url-row">
        <span id="base-url" class="base-url"></span>
        <input
            id="endpoint"
            type="text"
            aria-label="API endpoint"
        >
    </div>

    <button id="fetch-button">Fetch JSON</button>

    <div id="requested-url"></div>

    <pre id="output">Click the button to fetch data.</pre>

    <script>
        const DEFAULT_ENDPOINT = {default_endpoint_js};

        const baseUrlElement = document.getElementById("base-url");
        const endpointInput = document.getElementById("endpoint");
        const button = document.getElementById("fetch-button");
        const requestedUrl = document.getElementById("requested-url");
        const output = document.getElementById("output");

        const pagePath = window.location.pathname.replace(/\\/$/, "");
        const API_BASE_URL = `${{pagePath}}/api`;

        baseUrlElement.textContent =
            API_BASE_URL.replace(/\\/$/, "") + "/";

        endpointInput.value = DEFAULT_ENDPOINT;

        function buildUrl() {{
            const baseUrl = API_BASE_URL.replace(/\\/$/, "");
            const endpoint = endpointInput.value
                .trim()
                .replace(/^\\/+/, "");

            return `${{baseUrl}}/${{endpoint}}`;
        }}

        async function fetchJson() {{
            output.classList.remove("error");
            output.textContent = "Loading...";

            const url = buildUrl();
            requestedUrl.textContent = `Requesting: ${{url}}`;

            try {{
                const response = await fetch(url);

                if (!response.ok) {{
                    throw new Error(
                        `HTTP ${{response.status}}: ` +
                        `${{response.statusText}}`
                    );
                }}

                const data = await response.json();

                output.textContent = JSON.stringify(data, null, 2);
            }} catch (error) {{
                output.classList.add("error");
                output.textContent =
                    `Unable to fetch data: ${{error.message}}`;
            }}
        }}

        button.addEventListener("click", fetchJson);

        endpointInput.addEventListener("keydown", (event) => {{
            if (event.key === "Enter") {{
                fetchJson();
            }}
        }});
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return create_html_page()


@app.get("/api/{endpoint:path}")
def proxy_api(endpoint: str) -> Response:
    """Forward same-origin browser calls to the local API service.

    The browser calls consumer.py on /api/...; consumer.py then calls
    fast_api.py from Python. CORS applies to browser-to-server calls, not to
    this server-to-server Python call.
    """
    if not endpoint:
        raise HTTPException(status_code=400, detail="Endpoint is required")

    upstream_url = f"{API_BASE_URL}/{endpoint.strip('/')}"

    try:
        with urlopen(upstream_url, timeout=10) as upstream:
            return Response(
                content=upstream.read(),
                status_code=upstream.status,
                headers={
                    "content-type": upstream.headers.get(
                        "content-type",
                        "application/json",
                    ),
                },
            )
    except HTTPError as error:
        return Response(
            content=error.read(),
            status_code=error.code,
            headers={
                "content-type": error.headers.get(
                    "content-type",
                    "text/plain",
                ),
            },
        )
    except URLError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach API: {error.reason}",
        ) from error
