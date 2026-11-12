from typing import Any

from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference


app = FastAPI()


@app.get("/shipment")
def get_shipment():
    return {
        "content": "wooden table",
        "status": "in transit"
    }


@app.get("/shipment/{id}")
def get_shipment(id: str) -> dict[str, Any]:
    if id.isdecimal():
        return {
            "id": id,
            "type": "int",
            "weight": 123.55,
            "content": "wooden table",
            "status": "in transit"
        }
    return {
        "id": id,
        "type": "str",
        "content": "wooden table",
        "status": "in transit"
    }

@app.get("/shipment/{id}")
def get_shipment(id: str):
    return {
        "id": id,
        "type": "str",
        "content": "wooden table",
        "status": "in transit"
    }


@app.get("/scalar")
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API"
    )