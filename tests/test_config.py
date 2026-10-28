from devgenie import config
from devgenie.config import load_config


def test_defaults_when_no_files(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "USER_CONFIG", tmp_path / "nope-user.toml")
    monkeypatch.setattr(config, "PROJECT_CONFIG", tmp_path / "nope-project.toml")
    monkeypatch.delenv("DEVGENIE_PROVIDER", raising=False)
    cfg = load_config()
    assert cfg["provider"] == "ollama"
    assert cfg["ollama"]["model"] == "llama3"


def test_project_config_overrides_provider(monkeypatch, tmp_path):
    project = tmp_path / ".devgenie.toml"
    project.write_text('provider = "openai"\n[openai]\nmodel = "gpt-4o"\n', encoding="utf-8")
    monkeypatch.setattr(config, "USER_CONFIG", tmp_path / "nope-user.toml")
    monkeypatch.setattr(config, "PROJECT_CONFIG", project)
    monkeypatch.delenv("DEVGENIE_PROVIDER", raising=False)
    cfg = load_config()
    assert cfg["provider"] == "openai"
    assert cfg["openai"]["model"] == "gpt-4o"
    assert cfg["ollama"]["model"] == "llama3"  # deep merge keeps defaults


def test_env_overrides_file(monkeypatch, tmp_path):
    project = tmp_path / ".devgenie.toml"
    project.write_text('provider = "openai"\n', encoding="utf-8")
    monkeypatch.setattr(config, "USER_CONFIG", tmp_path / "nope-user.toml")
    monkeypatch.setattr(config, "PROJECT_CONFIG", project)
    monkeypatch.setenv("DEVGENIE_PROVIDER", "anthropic")
    cfg = load_config()
    assert cfg["provider"] == "anthropic"


def test_project_overrides_user(monkeypatch, tmp_path):
    user = tmp_path / "user.toml"
    user.write_text('provider = "openai"\n', encoding="utf-8")
    project = tmp_path / ".devgenie.toml"
    project.write_text('provider = "anthropic"\n', encoding="utf-8")
    monkeypatch.setattr(config, "USER_CONFIG", user)
    monkeypatch.setattr(config, "PROJECT_CONFIG", project)
    monkeypatch.delenv("DEVGENIE_PROVIDER", raising=False)
    cfg = load_config()
    assert cfg["provider"] == "anthropic"
