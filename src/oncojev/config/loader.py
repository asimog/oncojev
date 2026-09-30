from pathlib import Path
import yaml
from oncojev.config.models import ModelsConfig, RuntimeConfig
def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
def load_models_config(path: Path) -> ModelsConfig: return ModelsConfig.model_validate(load_yaml(path))
def load_runtime_config(path: Path) -> RuntimeConfig: return RuntimeConfig.model_validate(load_yaml(path))
