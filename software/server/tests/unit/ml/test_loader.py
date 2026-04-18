from bioliminal.ml.loader import ModelLoader, NoOpLoader


def test_noop_loader_reports_loaded_without_side_effects():
    loader = NoOpLoader()
    assert loader.name == "noop"
    assert loader.is_loaded() is True
    loader.load()
    assert loader.is_loaded() is True


def test_noop_loader_info_returns_dict_with_name():
    loader = NoOpLoader()
    info = loader.info()
    assert isinstance(info, dict)
    assert info["name"] == "noop"
    assert info["status"] == "loaded"


def test_noop_loader_duck_types_model_loader_protocol():
    loader: ModelLoader = NoOpLoader()
    assert hasattr(loader, "name")
    assert callable(loader.load)
    assert callable(loader.is_loaded)
    assert callable(loader.info)
