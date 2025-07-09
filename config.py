import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name('config.yaml')


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}

config = load_config()
