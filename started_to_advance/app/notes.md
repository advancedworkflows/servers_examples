# Scalar docs

```python
from scalar_fastapi import get_scalar_api_reference

@app.get("/scalar")
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API"
    )
```
