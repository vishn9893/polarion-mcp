from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SessionConfig(BaseModel):
    server_url: str = Field(alias="ServerUrl")
    username: str | None = Field(None, alias="Username")
    password: str | None = Field(None, alias="Password")
    project_id: str = Field(alias="ProjectId")
    timeout_seconds: float = Field(60.0, gt=0, alias="TimeoutSeconds")
    model_config = {"populate_by_name": True}


class ProjectConfig(BaseModel):
    project_url_alias: str = Field(alias="ProjectUrlAlias")
    default: bool = False
    session_config: SessionConfig = Field(alias="SessionConfig")
    blacklist_space_containing_match: str | None = Field(None, alias="BlacklistSpaceContainingMatch")
    polarion_work_item_types: list[dict[str, Any]] | None = Field(None, alias="PolarionWorkItemTypes")
    polarion_work_item_default_fields: list[str] | None = Field(None, alias="PolarionWorkItemDefaultFields")
    polarion_document_default_fields: list[str] | None = Field(None, alias="PolarionDocumentDefaultFields")
    model_config = {"populate_by_name": True}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="POLARION_", extra="ignore")
    url: str | None = None
    username: str | None = None
    password: str | None = None
    project_id: str | None = None
    config: str = "appsettings.json"
    project: str | None = None
    verify_tls: bool = True
    timeout: float = Field(60.0, gt=0)
    max_retries: int = Field(3, ge=0, le=10)
    transport: str = "stdio"

    def projects(self) -> list[ProjectConfig]:
        path = Path(self.config)
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            projects = [ProjectConfig.model_validate(item) for item in raw.get("PolarionProjects", [])]
            if projects:
                return projects
        if not self.url or not self.project_id:
            raise ValueError("Configure PolarionProjects in appsettings.json or POLARION_URL and POLARION_PROJECT_ID")
        return [ProjectConfig.model_validate({
            "ProjectUrlAlias": self.project or "default",
            "Default": True,
            "SessionConfig": {"ServerUrl": self.url, "Username": self.username,
                               "Password": self.password, "ProjectId": self.project_id,
                               "TimeoutSeconds": self.timeout},
        })]

    def selected_project(self) -> ProjectConfig:
        projects = self.projects()
        selected = next((p for p in projects if self.project and p.project_url_alias.lower() == self.project.lower()), None)
        return selected or next((p for p in projects if p.default), projects[0])

    def validate_auth(self) -> None:
        for project in self.projects():
            session = project.session_config
            if not session.server_url or not session.project_id:
                raise ValueError(f"Project '{project.project_url_alias}' is missing ServerUrl or ProjectId")
            if not (session.username and (session.password or os.getenv("POLARION_PASSWORD"))):
                raise ValueError(f"Project '{project.project_url_alias}' requires Username and Password")


@lru_cache
def get_settings() -> Settings:
    return Settings()
