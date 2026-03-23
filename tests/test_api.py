import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_index_page_renders():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "Hexloom" in response.text
    assert "Text to Format" in response.text
    assert "Format to Text" in response.text
    assert "/static/styles.css" in response.text
    assert 'property="og:title" content="Hexloom"' in response.text
    assert "/static/og-card.svg" in response.text
    assert "cdn.tailwindcss.com" not in response.text


@pytest.mark.asyncio
async def test_methods_endpoint_returns_method_catalog():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/methods")

    payload = response.json()
    assert response.status_code == 200
    assert "methods" in payload
    assert any(method["key"] == "base64" for method in payload["methods"])
    assert all("encode_input_label" in method for method in payload["methods"])


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok_report():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health/transformations")

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["checked_methods"] == 11
    assert payload["success_count"] == 11
    assert payload["error_count"] == 0
    assert all(item["status"] == "success" for item in payload["results"])


@pytest.mark.asyncio
async def test_favicon_returns_svg():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/favicon.ico")

    assert response.status_code == 200
    assert "svg" in response.text


@pytest.mark.asyncio
async def test_social_card_is_served():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/static/og-card.svg")

    assert response.status_code == 200
    assert "Hexloom" in response.text


@pytest.mark.asyncio
async def test_encode_endpoint_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/encode", json={"data": "Hello", "method": "rot13"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "result": "Uryyb",
        "clipboard_ready": True,
    }


@pytest.mark.asyncio
async def test_decode_endpoint_returns_400_on_invalid_data():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/decode", json={"data": "%%%??", "method": "base64"})

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "result": None,
        "message": "Geçerli bir Base64 metni bekleniyordu.",
        "clipboard_ready": False,
    }


@pytest.mark.asyncio
async def test_unknown_method_returns_400():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/encode", json={"data": "Hello", "method": "unknown"})

    assert response.status_code == 400
    assert response.json()["status"] == "error"
    assert "Bilinmeyen dönüşüm yöntemi" in response.json()["message"]


@pytest.mark.asyncio
async def test_bulk_decode_partial_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/bulk/decode",
            json={"method": "binary", "items": ["01001000 01101001", "0101010X"]},
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "partial_success"
    assert payload["summary"] == {"total": 2, "success_count": 1, "error_count": 1}
    assert payload["results"][0]["result"] == "Hi"
    assert payload["results"][1]["status"] == "error"


@pytest.mark.asyncio
async def test_encode_endpoint_validation_error_keeps_422():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/encode", json={"method": "rot13"})

    assert response.status_code == 422
