from pathlib import Path
from unittest.mock import Mock
import pytest
from app.exceptions import ConfigFileNotFound
from app.datastructures import Flags
from app.config import (
    load_config_from_file,
    save_config_to_file,
    ConfigSerializer,
    TomlConfigSerializer,
)


@pytest.fixture(scope="function")
def flags(config_path):
    return Flags(
        silent=True, config_path=config_path, log_level="debug", file=None, test=True
    )


class TestConfigSerializer:
    @pytest.fixture
    def expected_dict(self, test_config):
        return test_config.dict(exclude={"flags"})

    @pytest.fixture
    def mock_serializer(self, expected_dict):
        serializer_mock = Mock(spec=ConfigSerializer, name="serializer")
        serializer_mock.loads.return_value = expected_dict
        return serializer_mock

    @pytest.fixture(autouse=True)
    def config(self, flags, mock_serializer):
        return load_config_from_file(flags, serializer=mock_serializer)

    def test_load_config_file(self, mock_serializer: Mock):
        mock_serializer.loads.assert_called_once()

    def test_load_alerters(self, config):
        assert config.alerters["test_alerter_one"]["test_grp"] is True

    def test_load_monitoring(self, config):
        assert config.monitoring["test"]["test_key"] == "1234456788"

    def test_config_saving(self, test_config, expected_dict, mock_serializer: Mock):
        save_config_to_file(test_config, mock_serializer, "null_path")
        mock_serializer.dumps.assert_called_with("null_path", expected_dict)


class TestTomlConfigSerializer:
    @pytest.fixture(autouse=True)
    def no_saving(self, monkeypatch):
        monkeypatch.delattr("app.config.TomlConfigSerializer.dumps", raising=True)

    def test_config_file_not_found(self):
        with pytest.raises(ConfigFileNotFound):
            _flags = Flags(
                silent=True,
                config_path=str(Path.cwd() / "blah.toml"),
                log_level="debug",
                file=None,
                test=True,
            )
            load_config_from_file(_flags, TomlConfigSerializer())
