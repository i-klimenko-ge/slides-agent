import subprocess
import time

try:  # pragma: no cover - optional dependency
    import pyautogui
except Exception:  # pragma: no cover - fallback if pyautogui isn't available
    pyautogui = None

class PresentationViewer:
    """Base class for platform specific presentation viewers."""

    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.current_index: int | None = None
        self.path: str | None = None

    def open(self, path: str):
        raise NotImplementedError

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.process = None
        self.current_index = None

    def _press_key(self, key: str) -> None:
        """Press a keyboard key if possible."""
        if pyautogui is not None:  # pragma: no cover - optional dependency
            pyautogui.press(key)

    def goto_slide(self, index: int) -> None:
        """Navigate to a slide using left/right arrows."""
        if self.process is None:
            return

        start = self.current_index or 0
        steps = index - start
        if steps == 0:
            return

        key = "right" if steps > 0 else "left"
        for _ in range(abs(steps)):
            time.sleep(1)
            self._press_key(key)
        self.current_index = index

    def start_show(self):
        """Optional: start presentation in fullscreen."""
        if pyautogui is not None:
            pyautogui.press("f5")
            self.current_index = 0


class LinuxPresentationViewer(PresentationViewer):
    """Use libreoffice and xdotool on Linux."""

    def open(self, path: str):
        self.close()
        try:
            self.process = subprocess.Popen(["libreoffice", "--show", path])
        except Exception:
            # fallback
            self.process = subprocess.Popen(["xdg-open", path])
        self.current_index = 0
        self.path = path


    def _press_key(self, key: str) -> None:
        if pyautogui is not None:  # pragma: no cover - optional dependency
            pyautogui.press(key)
        else:
            subprocess.run(["xdotool", "key", key.capitalize()], check=False)

    def start_show(self):
        if pyautogui is not None:
            pyautogui.press("f5")
        else:
            subprocess.run(["xdotool", "key", "F5"], check=False)
        self.current_index = 0


class WindowsPresentationViewer(PresentationViewer):
    """Basic viewer for Windows using start command."""

    def open(self, path: str):
        self.close()
        self.process = subprocess.Popen(["start", "", path], shell=True)
        self.current_index = 0
        self.path = path

    def start_show(self):
        if pyautogui is not None:
            pyautogui.press("f5")
            self.current_index = 0


class MacPresentationViewer(PresentationViewer):
    """Viewer for macOS using open command."""

    def open(self, path: str):
        self.close()
        self.process = subprocess.Popen(["open", path])
        self.current_index = 0
        self.path = path

    def start_show(self):
        if pyautogui is not None:
            pyautogui.hotkey("fn", "f")
        self.current_index = 0


class MacPptxPresentationViewer(MacPresentationViewer):
    """Specialized viewer for pptx files on macOS."""

    def start_show(self):
        if pyautogui is not None:
            pyautogui.hotkey("command", "option", "p")
        self.current_index = 0


def get_viewer(os_type: str, path: str | None = None) -> PresentationViewer:
    """Return viewer instance depending on OS and file type."""
    if os_type.startswith("win"):
        return WindowsPresentationViewer()
    if os_type.startswith("darwin") or os_type == "mac":
        if path and path.lower().endswith(".pptx"):
            return MacPptxPresentationViewer()
        return MacPresentationViewer()
    return LinuxPresentationViewer()

