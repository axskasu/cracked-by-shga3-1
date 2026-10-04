from datetime import datetime
from typing import Any
from rich.console import Console
from rich.text import Text
from rich.traceback import install

install(show_locals=False)

MAX_LOGS = 30


class Logger:
    def __init__(self) -> None:
        self.console = Console(legacy_windows=False)
        self.debug_mode = False
        self.all_logs = []
        self.stats = {
            "bad": 0,
            "2fa": 0,
            "hit": 0,
            "skins": 0,
            "ogs": 0,
            "remain": 0,
        }
        self.colors = {
            "INFO": ((80, 180, 255), (130, 80, 255)),
            "SUCCESS": ((50, 255, 150), (50, 200, 100)),
            "WARNING": ((255, 220, 60), (255, 140, 40)),
            "ERROR": ((255, 100, 100), (255, 40, 40)),
            "DEBUG": ((180, 180, 180), (100, 100, 100)),
            "CRITICAL": ((255, 80, 180), (255, 40, 80)),
        }

    @staticmethod
    def _gradient_text(text: str, start: tuple[int, int, int], end: tuple[int, int, int]) -> Text:
        result = Text()
        progress_step = max(len(text) - 1, 1)
        for index, char in enumerate(text):
            progress = index / progress_step
            color = (
                int(start[0] + (end[0] - start[0]) * progress),
                int(start[1] + (end[1] - start[1]) * progress),
                int(start[2] + (end[2] - start[2]) * progress),
            )
            result.append(char, style=f"rgb({color[0]},{color[1]},{color[2]})")
        return result

    @staticmethod
    def _static_gradient_text(text: str) -> Text:
        return Logger._gradient_text(text, (255, 30, 30), (120, 0, 0))

    @staticmethod
    def _diagonal_gradient_text(
        text: str,
        start: tuple[int, int, int],
        end: tuple[int, int, int] = ((255, 30, 30), (100, 0, 0)),
    ) -> Text:
        result = Text()
        lines = text.split("\n")
        progress_height = max(len(lines) - 1, 1)
        progress_width = max(max((len(line) for line in lines), default=1) - 1, 1)
        for line_index, line in enumerate(lines):
            for char_index, char in enumerate(line):
                progress = (char_index / progress_width + line_index / progress_height) / 2
                color = (
                    int(start[0] + (end[0] - start[0]) * progress),
                    int(start[1] + (end[1] - start[1]) * progress),
                    int(start[2] + (end[2] - start[2]) * progress),
                )
                result.append(char, style=f"rgb({color[0]},{color[1]},{color[2]})")
            if line_index < len(lines) - 1:
                result.append("\n")
        return result

    def _log(self, level: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        start, end = self.colors[level]
        text = Text()
        text.append(f"[{timestamp}] ", style="dim")
        text.append(self._gradient_text(f"[{level}]", start, end))
        text.append(f" {message}")
        self.all_logs.append(text)
        if len(self.all_logs) > MAX_LOGS:
            self.all_logs.pop(0)

    def info(self, message: str, *args: Any) -> None:
        if args:
            message = message % args
        self._log("INFO", message)

    def success(self, message: str) -> None:
        self._log("SUCCESS", message)

    def warning(self, message: str) -> None:
        self._log("WARNING", message)

    def error(self, message: str) -> None:
        self._log("ERROR", message)

    def debug(self, message: str, *args: Any) -> None:
        if not self.debug_mode:
            return
        if args:
            message = message % args
        self._log("DEBUG", message)

    def critical(self, message: str) -> None:
        self._log("CRITICAL", message)

    def update_stat(self, key: str, amount: int = 1) -> None:
        if key in self.stats:
            self.stats[key] += amount


logger = Logger()