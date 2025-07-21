import subprocess

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

    def goto_slide(self, index: int):
        raise NotImplementedError

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

    def goto_slide(self, index: int):
        if self.process is None:
            return
        if pyautogui is not None:
            for ch in str(index + 1):
                pyautogui.press(ch)
            pyautogui.press("enter")
        else:
            steps = index - (self.current_index or 0)
            key = "Right" if steps > 0 else "Left"
            for _ in range(abs(steps)):
                subprocess.run(["xdotool", "key", key], check=False)
        self.current_index = index

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

    def goto_slide(self, index: int):
        if pyautogui is not None:
            for ch in str(index + 1):
                pyautogui.press(ch)
            pyautogui.press("enter")
        self.current_index = index

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

    def goto_slide(self, index: int):
        if pyautogui is not None:
            for ch in str(index + 1):
                pyautogui.press(ch)
            pyautogui.press("enter")
        self.current_index = index

    def start_show(self):
        if pyautogui is not None:
            if self.path and self.path.lower().endswith(".pptx"):
                pyautogui.hotkey("command", "option", "p")
            else:
                pyautogui.hotkey("fn", "f5")
            self.current_index = 0


def get_viewer(os_type: str) -> PresentationViewer:
    if os_type.startswith("win"):
        return WindowsPresentationViewer()
    if os_type.startswith("darwin") or os_type == "mac":
        return MacPresentationViewer()
    return LinuxPresentationViewer()
