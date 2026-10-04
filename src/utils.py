"""EpicChecker - src.utils.

Reconstructed from the PyArmor-stripped bytecode (utils.pyc.1shot.das).
File resolution for combo lists, combo loading, and combo removal.
"""

import os
import threading
from pathlib import Path

from src.config import config
from src.logger import logger

_combo_file_lock = threading.Lock()


def get_combo_files() -> list[Path]:
    """
    Résout intelligemment les fichiers de combos, que le chemin configuré
    soit un fichier direct ou un dossier (ex: 'input/' ou 'input').
    """
    raw = config.get("paths.combo_file", "input/combo.txt")
    if not raw or not str(raw).strip():
        raw = "input/combo.txt"

    combo_path = Path(str(raw).strip().strip('"').strip("'"))

    if combo_path.exists() and combo_path.is_dir():
        candidates = [
            "combo.txt",
            "combos.txt",
            "combo_list.txt",
            "combolist.txt",
            "comptes.txt",
        ]
        found = []
        for name in candidates:
            candidate = combo_path / name
            if candidate.exists() and candidate.is_file():
                found.append(candidate)
        if found:
            return found

        txt_files = [
            f
            for f in combo_path.glob("*.txt")
            if f.is_file()
            and f.name.lower() not in ("rare_skin.txt", "rare_skins.txt", "rares.txt")
        ]
        if txt_files:
            return txt_files

        combo_file = combo_path / "combo.txt"
        try:
            combo_file.touch(exist_ok=True)
        except Exception:
            pass
        return [combo_file]

    if combo_path.exists() and combo_path.is_file():
        return [combo_path]

    if raw.endswith(("/", "\\")) or combo_path.suffix == "":
        try:
            combo_path.mkdir(parents=True, exist_ok=True)
            combo_file = combo_path / "combo.txt"
            combo_file.touch(exist_ok=True)
            return [combo_file]
        except Exception:
            pass

    for candidate in (
        Path("input/combo.txt"),
        Path("input/combos.txt"),
        Path("combo.txt"),
        Path("combos.txt"),
    ):
        if candidate.exists() and candidate.is_file():
            return [candidate]

    return [combo_path]


def load_combos() -> list[tuple[str, str]]:
    combo_files = get_combo_files()
    combos = []
    seen = set()
    for combo_file in combo_files:
        if not combo_file.exists():
            continue
        if combo_file.is_dir():
            continue
        try:
            with combo_file.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or ":" not in line:
                        continue
                    email, password = line.split(":", 1)
                    email = email.strip()
                    password = password.strip()
                    combo = (email, password)
                    if email and password and combo not in seen:
                        seen.add(combo)
                        combos.append(combo)
        except Exception as e:
            logger.error(
                f"Erreur lors de la lecture du fichier combos ({combo_file}): {e}"
            )
    return combos


def remove_combo(username: str, password: str) -> None:
    combo_files = get_combo_files()
    username_key = username.strip().lower()
    password_key = password.strip()

    with _combo_file_lock:
        for combo_file in combo_files:
            if not combo_file.exists() or combo_file.is_dir():
                continue
            tmp_path = None
            try:
                with combo_file.open("r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                remaining = []
                found = False
                for line in lines:
                    stripped = line.strip()
                    if (
                        not stripped
                        or stripped.startswith("#")
                        or ":" not in stripped
                    ):
                        remaining.append(line)
                        continue
                    parts = stripped.split(":", 1)
                    file_email = parts[0].strip().lower()
                    file_pass = parts[1].strip()
                    if (
                        not found
                        and file_email == username_key
                        and file_pass == password_key
                    ):
                        found = True
                        continue
                    remaining.append(line)
                if found:
                    parent_dir = combo_file.parent
                    parent_dir.mkdir(parents=True, exist_ok=True)
                    tmp_path = (
                        parent_dir
                        / f".tmp_combo_{os.getpid()}_{threading.get_ident()}.tmp"
                    )
                    with tmp_path.open("w", encoding="utf-8") as f:
                        f.writelines(remaining)
                    os.replace(tmp_path, combo_file)
                    break
            except Exception as e:
                logger.debug(f"Erreur suppression combo dans {combo_file}: {e}")
                try:
                    if tmp_path and tmp_path.exists():
                        tmp_path.unlink()
                except Exception:
                    pass