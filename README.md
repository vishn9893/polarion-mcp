# Polarion MCP

An async Python MCP server adapting the tool surface of `PolarionMcpServers-0.16.0` to Polarion’s REST API. It supports stdio, SSE, and streamable HTTP transports and can select one of multiple configured Polarion projects by alias.

## Configuration

The reference configuration format is supported through `appsettings.json`:

```json
{
  "PolarionProjects": [
    {
      "ProjectUrlAlias": "default",
      "Default": true,
      "SessionConfig": {
        "ServerUrl": "https://polarion.example.com",
        "Username": "read-only-user",
        "Password": "use-POLARION_PASSWORD-instead",
        "ProjectId": "my_project",
        "TimeoutSeconds": 60
      }
    }
  ]
}
```

`POLARION_PASSWORD` overrides configured passwords. For a single project, the shorter environment configuration is also available: `POLARION_URL`, `POLARION_USERNAME`, `POLARION_PROJECT_ID`, and `POLARION_PASSWORD`.

## Run

```bash
cd polarion-mcp
uv sync
POLARION_PASSWORD='secret' uv run polarion-mcp
```

Select a configured alias with `POLARION_PROJECT=alias`. The MCP tools mirror the reference implementation, including document, section, work-item, revision, type, and search operations.
