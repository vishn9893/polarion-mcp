import httpx
import pytest

from polarion_mcp.client import PolarionClient
from polarion_mcp.config import Settings
from polarion_mcp.tools import get_sections_in_document


@pytest.mark.asyncio
async def test_document_sections_filter_headings():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/projects/demo/spaces/req/documents/spec/workitems")
        return httpx.Response(200, json={"data": [
            {"id": "h1", "attributes": {"type": "heading", "outlineNumber": "1", "title": "Intro"}},
            {"id": "r1", "attributes": {"type": "requirement", "title": "Text"}},
        ]})

    settings = Settings(url="https://polarion.example", username="user", password="pass", project_id="demo")
    async with PolarionClient(settings, http=httpx.AsyncClient(base_url="https://polarion.example", transport=httpx.MockTransport(handler))) as client:
        result = await get_sections_in_document(client, "req", "spec")
    assert result == "1 Intro"
