from __future__ import annotations

import json
import re
from typing import Any

from .client import PolarionClient


def _data(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("data"), list): return payload["data"]
    if isinstance(payload, list): return payload
    return [payload] if isinstance(payload, dict) else []


def _attr(item: dict[str, Any], key: str, default: Any = "N/A") -> Any:
    return item.get("attributes", {}).get(key, item.get(key, default))


def _markdown(items: list[dict[str, Any]], title: str) -> str:
    lines = [f"# {title}", ""]
    for item in items:
        lines += [f"## WorkItem (id={item.get('id', 'N/A')}, type={_attr(item, 'type')})", "",
                  f"- **Title**: {_attr(item, 'title')}", f"- **Status**: {_attr(item, 'status')}",
                  f"- **Outline Number**: {_attr(item, 'outlineNumber')}", ""]
        description = _attr(item, "description", "")
        if description: lines += ["### Description", "", str(description), ""]
    return "\n".join(lines)


async def get_text_for_workitems_by_id(c: PolarionClient, workitem_ids: str) -> str:
    ids = [x.strip() for x in workitem_ids.split(",") if x.strip()]
    return _markdown([await c.get(f"/projects/{c.project.session_config.project_id}/workitems/{i}") for i in ids], "Work Item Text")

async def get_text_for_workitem_at_revision(c: PolarionClient, workitem_id: str, revision: str) -> str:
    item = await c.get(f"/projects/{c.project.session_config.project_id}/workitems/{workitem_id}/revisions/{revision}")
    return _markdown([item], f"Work Item {workitem_id} at Revision {revision}")

async def get_document_info(c: PolarionClient, space: str, document_id: str, custom_fields: str = "none") -> str:
    return json.dumps(await c.get(f"/projects/{c.project.session_config.project_id}/spaces/{space}/documents/{document_id}"), indent=2)

async def get_details_for_workitems(c: PolarionClient, workitem_ids: str) -> str:
    return json.dumps([await c.get(f"/projects/{c.project.session_config.project_id}/workitems/{i.strip()}") for i in workitem_ids.split(",") if i.strip()], indent=2)

async def get_workitems_in_module(c: PolarionClient, space: str, document_id: str,
                                  item_types: str | None = None, revision: str = "-1") -> str:
    params: dict[str, Any] = {}
    if revision != "-1": params["revision"] = revision
    if item_types and revision == "-1": params["types"] = item_types
    items = _data(await c.get(f"/projects/{c.project.session_config.project_id}/spaces/{space}/documents/{document_id}/workitems", params=params or None))
    return _markdown(items, f"Work Items in {space}/{document_id}")

async def get_documents(c: PolarionClient, space: str | None = None, title_filter: str | None = None) -> Any:
    if space:
        docs = _data(await c.get(f"/projects/{c.project.session_config.project_id}/spaces/{space}/documents"))
        return [d for d in docs if not title_filter or title_filter.lower() in str(_attr(d, "title", "")).lower()]
    result = await list_spaces(c)
    docs = []
    for space in result:
        docs.extend(_data(await c.get(f"/projects/{c.project.session_config.project_id}/spaces/{space}/documents")))
    return [d for d in docs if not title_filter or title_filter.lower() in str(_attr(d, "title", "")).lower()]

async def get_documents_by_space_names(c: PolarionClient, space_names: str) -> Any:
    pid = c.project.session_config.project_id
    result = []
    for space in [x.strip() for x in space_names.split(",") if x.strip()]: result.extend(_data(await c.get(f"/projects/{pid}/spaces/{space}/documents")))
    return result

async def list_spaces(c: PolarionClient) -> list[str]:
    result = await c.get(f"/projects/{c.project.session_config.project_id}/spaces")
    return [str(_attr(x, "name", x.get("id", ""))) for x in _data(result) if not c.project.blacklist_space_containing_match or c.project.blacklist_space_containing_match.lower() not in str(_attr(x, "name", "")).lower()]

async def get_sections_in_document(c: PolarionClient, space: str, document_id: str, revision: str = "-1") -> str:
    items = _data(await c.get(f"/projects/{c.project.session_config.project_id}/spaces/{space}/documents/{document_id}/workitems", params={"revision": revision} if revision != "-1" else None))
    return "\n".join(f"{_attr(x, 'outlineNumber', '')} {_attr(x, 'title')}" for x in items if str(_attr(x, "type", "")).lower() == "heading") or "No headings found."

async def get_section_content_for_document(c: PolarionClient, space: str, document_id: str, section_id: str, revision: str = "-1") -> str:
    items = _data(await c.get(f"/projects/{c.project.session_config.project_id}/spaces/{space}/documents/{document_id}/workitems", params={"revision": revision} if revision != "-1" else None))
    return _markdown([x for x in items if str(x.get("id")) == section_id or str(_attr(x, "outlineNumber", "")) == section_id], f"Section {section_id}")

async def search_workitems_in_document(c: PolarionClient, space: str, document_id: str, search_query: str, revision: str = "-1") -> str:
    items = _data(await c.get(f"/projects/{c.project.session_config.project_id}/spaces/{space}/documents/{document_id}/workitems", params={"revision": revision} if revision != "-1" else None))
    terms = [x for x in re.split(r"\s+", search_query.strip()) if x]
    matches = [x for x in items if any(t.lower() in json.dumps(x).lower() for t in terms)]
    return _markdown(matches, "Document Search Results") if matches else f"No work items matching '{search_query}' found."

async def list_available_custom_fields_for_workitem_types(c: PolarionClient, item_types: str) -> Any:
    return [x for x in (c.project.polarion_work_item_types or []) if x.get("id", "").lower() in {t.strip().lower() for t in item_types.split(",")}]

async def list_available_workitem_types(c: PolarionClient) -> Any:
    configured = c.project.polarion_work_item_types or []
    return [item.get("id") for item in configured if item.get("id")]

async def get_revisions_list_for_workitem(c: PolarionClient, workitem_id: str) -> Any:
    return await c.get(f"/projects/{c.project.session_config.project_id}/workitems/{workitem_id}/revisions")

async def get_revisions_content_for_workitem(c: PolarionClient, workitem_id: str, revisions: str | None = None) -> str:
    result = await get_revisions_list_for_workitem(c, workitem_id)
    values = _data(result)
    if revisions: values = [x for x in values if str(x.get("id")) in {r.strip() for r in revisions.split(",")}]
    return _markdown(values, f"Revision Content for {workitem_id}")

# Names used by the newer reference release.
async def get_workitem(c: PolarionClient, workitem_id: str) -> str:
    return await get_text_for_workitems_by_id(c, workitem_id)

async def get_workitem_details(c: PolarionClient, workitem_id: str, **_: Any) -> str:
    return await get_details_for_workitems(c, workitem_id)

async def get_workitem_history(c: PolarionClient, workitem_id: str, limit: int = 5) -> str:
    result = _data(await get_revisions_list_for_workitem(c, workitem_id))
    if limit != -1: result = result[:max(0, limit)]
    return _markdown(result, f"Revision History for {workitem_id}") if result else f"No revisions found for '{workitem_id}'."
list_documents = get_documents
list_workitem_types = list_available_workitem_types
get_document_outline = get_sections_in_document
get_document_section = get_section_content_for_document
get_document_revision_history = lambda c, space, document_id, limit=10: c.get(f"/projects/{c.project.session_config.project_id}/spaces/{space}/documents/{document_id}/revisions", params={"page[size]": limit})
search_in_document = search_workitems_in_document
search_workitems = lambda c, search_query, **kwargs: c.get(f"/projects/{c.project.session_config.project_id}/workitems", params={"query": search_query, **kwargs})
list_custom_fields = lambda c, workitem_type: list_available_custom_fields_for_workitem_types(c, workitem_type)
