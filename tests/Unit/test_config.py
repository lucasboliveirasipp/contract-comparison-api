import os

from src.config import load_config


def _write(path, content):
    path.write_text(content, encoding="utf-8")


def test_load_config_loads_values_from_dsv_files(tmp_path, monkeypatch):
    monkeypatch.delenv("FOO_VAR", raising=False)
    _write(tmp_path / "variables.DSV", "FOO_VAR=from-variables\n")

    loaded = load_config(root=tmp_path)

    assert os.getenv("FOO_VAR") == "from-variables"
    assert "variables.DSV" in loaded


def test_load_config_loads_secrets_file(tmp_path, monkeypatch):
    monkeypatch.delenv("SECRET_VAR", raising=False)
    _write(tmp_path / "secrets.DSV", "SECRET_VAR=shh\n")

    load_config(root=tmp_path)

    assert os.getenv("SECRET_VAR") == "shh"


def test_load_config_does_not_override_existing_env(tmp_path, monkeypatch):
    # L12/pipeline: variável já definida no ambiente publicado deve VENCER o arquivo
    monkeypatch.setenv("ALREADY_SET", "from-environment")
    _write(tmp_path / "variables.DSV", "ALREADY_SET=from-file\n")

    load_config(root=tmp_path)

    assert os.getenv("ALREADY_SET") == "from-environment"


def test_load_config_missing_files_does_not_raise(tmp_path):
    # diretório sem nenhum .DSV — não pode quebrar
    loaded = load_config(root=tmp_path)
    assert loaded == []


def test_load_config_variables_win_over_secrets_for_same_key(tmp_path, monkeypatch):
    monkeypatch.delenv("DUP_KEY", raising=False)
    _write(tmp_path / "variables.DSV", "DUP_KEY=from-variables\n")
    _write(tmp_path / "secrets.DSV", "DUP_KEY=from-secrets\n")

    load_config(root=tmp_path)

    # variables.DSV é carregado primeiro; com override=False, vence
    assert os.getenv("DUP_KEY") == "from-variables"
