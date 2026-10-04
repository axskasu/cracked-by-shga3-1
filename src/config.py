import os
import json
from pathlib import Path
from typing import Any
from logger import logger

appdata = os.environ.get("APPDATA", str(Path.home()))

CONFIG_DIR = Path(appdata) / "sicachecker"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "debug": True,
    "threads": 3,
    "paths": {
        "combo_file": "input/combo.txt",
        "output_folder": "output/",
        "rare_skins_file": "input/rare_skin.txt",
    },
    "webhooks": {
        "live_url": "",
        "hit_url": "",
        "twofa_url": "",
        "shortcode_url": "",
        "screenshot_url": "",
    },
}


class Config:
    def __init__(self, path: Path = CONFIG_FILE) -> None:
        self.path = path
        self.data = {}
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            config_json = Path("config.json")
            if config_json.exists():
                try:
                    with open(config_json, "r", encoding="utf-8") as f:
                        self.data = json.load(f)
                except Exception:
                    self.data = json.loads(json.dumps(DEFAULT_CONFIG))
            else:
                self.data = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in self.data:
                    self.data[key] = value
                elif isinstance(value, dict) and isinstance(self.data[key], dict):
                    for sub_key, sub_value in value.items():
                        if sub_key not in self.data[key]:
                            self.data[key][sub_key] = sub_value
        except Exception as e:
            logger.error(f"Erreur chargement configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        current = self.data
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set(self, key: str, value: Any) -> None:
        parts = key.split(".")
        current = self.data
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            try:
                with open("config.json", "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=4)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration: {e}")


config = Config()