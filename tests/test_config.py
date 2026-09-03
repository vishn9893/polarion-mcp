from polarion_mcp.config import Settings


def test_single_project_environment_configuration():
    settings = Settings(url="https://polarion.example", username="user", password="pass", project_id="demo")
    project = settings.selected_project()
    assert project.project_url_alias == "default"
    assert project.session_config.project_id == "demo"
