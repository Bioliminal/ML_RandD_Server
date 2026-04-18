import pytest

from bioliminal.ml.loader import NoOpLoader
from bioliminal.models.registry import REGISTRY, ModelRegistry


def test_register_and_get_loader():
    reg = ModelRegistry()
    loader = NoOpLoader()
    reg.register(loader)
    assert reg.is_registered("noop")
    assert reg.get("noop") is loader


def test_get_unknown_loader_raises_key_error():
    reg = ModelRegistry()
    with pytest.raises(KeyError):
        reg.get("does_not_exist")


def test_register_is_idempotent_last_wins():
    reg = ModelRegistry()
    first = NoOpLoader()
    second = NoOpLoader()
    reg.register(first)
    reg.register(second)
    assert reg.get("noop") is second


def test_loaded_models_lists_registered_loader_names():
    reg = ModelRegistry()
    reg.register(NoOpLoader())
    assert reg.loaded_models() == ["noop"]


def test_module_level_registry_is_a_model_registry_instance():
    assert isinstance(REGISTRY, ModelRegistry)
