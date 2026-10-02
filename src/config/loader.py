from pathlib import Path
import yaml
from src.config.models import ModelsConfig, RuntimeConfig
from src.config.environment import process_settings
def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
def load_models_config(path: Path) -> ModelsConfig: return ModelsConfig.model_validate(load_yaml(path))
def load_runtime_config(path: Path, *, testing: bool | None = None) -> RuntimeConfig:
    if testing is None:
        testing = process_settings(path.resolve().parents[1]).testing
    ordinary = RuntimeConfig.model_validate(load_yaml(path))
    if not testing:
        return ordinary
    values = ordinary.model_dump()
    block, caps = values["block"], ordinary.testing.block
    block["max_seconds"] = min(block["max_seconds"], caps.max_seconds)
    block["min_seconds"] = min(block["min_seconds"], caps.min_seconds, block["max_seconds"])
    block["default_seconds"] = min(block["default_seconds"], caps.default_seconds, block["max_seconds"])
    block["handoff_reserve_seconds"] = min(block["handoff_reserve_seconds"], caps.handoff_reserve_seconds,
                                           block["min_seconds"] - 1)
    data = values["testing"]["public_data"]
    data["max_response_bytes"] = min(data["max_response_bytes"], ordinary.block.max_download_bytes)
    data["max_block_download_bytes"] = min(data["max_block_download_bytes"], ordinary.resources.max_block_download_bytes)
    data["max_service_download_bytes"] = min(data["max_service_download_bytes"], ordinary.resources.max_service_download_bytes)
    effective = RuntimeConfig.model_validate(values)
    effective._testing_enabled = True
    return effective
