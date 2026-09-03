from __future__ import annotations

import argparse
import os
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Awaitable, Callable

from mcp.server.fastmcp import FastMCP

from .client import PolarionClient
from .config import get_settings
from . import tools


@asynccontextmanager
async def _client():
    async with PolarionClient(get_settings()) as client:
        yield client


def _api(fn: Callable[..., Awaitable[Any]]):
    @wraps(fn)
    async def wrapped(*args: Any, **kwargs: Any) -> Any:
        async with _client() as client:
            return await fn(client, *args, **kwargs)
    return wrapped


mcp = FastMCP("polarion-mcp", instructions="Polarion ALM REST API tools based on PolarionMcpServers reference implementation.")


def _register(name: str, fn: Callable[..., Awaitable[Any]], **defaults: Any) -> None:
    async def handler(**kwargs: Any) -> Any:
        return await _api(fn)(**{**defaults, **kwargs})
    handler.__name__ = name
    mcp.tool(name=name)(handler)


@mcp.tool(name="get_text_for_workitems_by_id")
async def get_text_for_workitems_by_id(workitem_ids: str) -> str:
    return await _api(tools.get_text_for_workitems_by_id)(workitem_ids)


@mcp.tool(name="get_text_for_workitem_at_revision")
async def get_text_for_workitem_at_revision(workitem_id: str, revision: str) -> str:
    return await _api(tools.get_text_for_workitem_at_revision)(workitem_id, revision)


@mcp.tool(name="get_details_for_workitems")
async def get_details_for_workitems(workitem_ids: str) -> str:
    return await _api(tools.get_details_for_workitems)(workitem_ids)

@mcp.tool(name="get_document_info")
async def get_document_info(space: str, document_id: str, custom_fields: str = "none") -> str:
    return await _api(tools.get_document_info)(space, document_id, custom_fields)


@mcp.tool(name="get_documents")
async def get_documents(space: str | None = None, title_filter: str | None = None) -> Any:
    return await _api(tools.get_documents)(space, title_filter)


@mcp.tool(name="get_documents_by_space_names")
async def get_documents_by_space_names(space_names: str) -> Any:
    return await _api(tools.get_documents_by_space_names)(space_names)


@mcp.tool(name="get_space_names")
async def get_space_names() -> Any:
    return await _api(tools.list_spaces)()


@mcp.tool(name="get_sections_in_document")
async def get_sections_in_document(space: str, document_id: str, revision: str = "-1") -> str:
    return await _api(tools.get_sections_in_document)(space, document_id, revision)

@mcp.tool(name="get_workitems_in_module")
async def get_workitems_in_module(space: str, document_id: str, item_types: str | None = None, revision: str = "-1") -> str:
    return await _api(tools.get_workitems_in_module)(space, document_id, item_types, revision)


@mcp.tool(name="get_section_content_for_document")
async def get_section_content_for_document(space: str, document_id: str, section_id: str, revision: str = "-1") -> str:
    return await _api(tools.get_section_content_for_document)(space, document_id, section_id, revision)


@mcp.tool(name="search_workitems_in_document")
async def search_workitems_in_document(space: str, document_id: str, search_query: str, revision: str = "-1") -> str:
    return await _api(tools.search_workitems_in_document)(space, document_id, search_query, revision)


@mcp.tool(name="list_available_custom_fields_for_workitem_types")
async def list_available_custom_fields_for_workitem_types(item_types: str) -> Any:
    return await _api(tools.list_available_custom_fields_for_workitem_types)(item_types)


@mcp.tool(name="list_available_workitem_types")
async def list_available_workitem_types() -> Any:
    return await _api(tools.list_available_workitem_types)()


@mcp.tool(name="get_revisions_list_for_workitem")
async def get_revisions_list_for_workitem(workitem_id: str) -> Any:
    return await _api(tools.get_revisions_list_for_workitem)(workitem_id)


@mcp.tool(name="get_revisions_content_for_workitem")
async def get_revisions_content_for_workitem(workitem_id: str, revisions: str | None = None) -> str:
    return await _api(tools.get_revisions_content_for_workitem)(workitem_id, revisions)


# Names introduced by the 0.16.0 reference tool split.
@mcp.tool(name="get_workitem")
async def get_workitem(workitem_id: str, revision: str | None = None) -> Any:
    if revision and revision != "-1":
        return await _api(tools.get_text_for_workitem_at_revision)(workitem_id, revision)
    return await _api(tools.get_workitem)(workitem_id)


@mcp.tool(name="get_workitem_details")
async def get_workitem_details(workitem_id: str) -> str:
    return await _api(tools.get_workitem_details)(workitem_id)


@mcp.tool(name="get_workitem_history")
async def get_workitem_history(workitem_id: str, limit: int = 5) -> str:
    return await _api(tools.get_workitem_history)(workitem_id, limit=limit)


@mcp.tool(name="list_documents")
async def list_documents(space: str | None = None, title_filter: str | None = None) -> Any:
    return await _api(tools.list_documents)(space, title_filter)


@mcp.tool(name="list_spaces")
async def list_spaces() -> Any:
    return await _api(tools.list_spaces)()


@mcp.tool(name="list_workitem_types")
async def list_workitem_types() -> Any:
    return await _api(tools.list_workitem_types)()

@mcp.tool(name="list_custom_fields")
async def list_custom_fields(workitem_type: str) -> Any:
    return await _api(tools.list_custom_fields)(workitem_type)


@mcp.tool(name="get_document_outline")
async def get_document_outline(space: str, document_id: str, revision: str = "-1") -> str:
    return await _api(tools.get_document_outline)(space, document_id, revision)


@mcp.tool(name="get_document_section")
async def get_document_section(space: str, document_id: str, section_id: str, revision: str = "-1") -> str:
    return await _api(tools.get_document_section)(space, document_id, section_id, revision)


@mcp.tool(name="get_document_revision_history")
async def get_document_revision_history(space: str, document_id: str, limit: int = 10) -> Any:
    return await _api(tools.get_document_revision_history)(space, document_id, limit)


@mcp.tool(name="search_in_document")
async def search_in_document(space: str, document_id: str, search_query: str, revision: str = "-1") -> str:
    return await _api(tools.search_in_document)(space, document_id, search_query, revision)


@mcp.tool(name="search_workitems")
async def search_workitems(search_query: str, item_types: str | None = None, status_filter: str | None = None,
                           sort_by: str = "created", max_results: int = 50) -> Any:
    return await _api(tools.search_workitems)(search_query, item_types=item_types, status_filter=status_filter,
                                              sort_by=sort_by, max_results=max_results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Polarion MCP server")
    parser.add_argument("--project", "-p", help="configured Polarion project alias")
    parser.add_argument("--config", "-c", help="reference-format appsettings.json path")
    args = parser.parse_args()
    if args.project:
        os.environ["POLARION_PROJECT"] = args.project
    if args.config:
        os.environ["POLARION_CONFIG"] = args.config
    settings = get_settings()
    if settings.transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("POLARION_TRANSPORT must be stdio, sse, or streamable-http")
    settings.validate_auth()
    mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
