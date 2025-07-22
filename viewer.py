import subprocess
import time
import pyautogui

class PresentationViewer:
    """Base class for platform specific presentation viewers."""

    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.current_num: int | None = None
        self.path: str | None = None

    def open(self, path: str):
        raise NotImplementedError

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.process = None
        self.current_num = None

    def _press_key(self, key: str) -> None:
        pyautogui.press(key)
        print(key)

    def _press_hotkey(self, *args) -> None:
        pyautogui.hotkey(args)
        print("+".join(args))

    def goto_slide(self, num: int) -> None:
        """Navigate to a slide using left/right arrows."""
        if self.process is None:
            return

        start = self.current_num or 1
        steps = num - start
        if steps == 0:
            return

        key = "right" if steps > 0 else "left"
        for _ in range(abs(steps)):
            time.sleep(1)
            self._press_key(key)
        self.current_num = num

    def start_show(self):
        """Optional: start presentation in fullscreen."""
        self._press_key("f5")
        self.current_num = 0


class LinuxPresentationViewer(PresentationViewer):
    """Use libreoffice and xdotool on Linux."""

    def open(self, path: str):
        self.close()
        try:
            self.process = subprocess.Popen(["libreoffice", "--show", path])
        except Exception:
            # fallback
            self.process = subprocess.Popen(["xdg-open", path])
        self.current_num = 0
        self.path = path


class WindowsPresentationViewer(PresentationViewer):
    """Basic viewer for Windows using start command."""

    def open(self, path: str):
        self.close()
        self.process = subprocess.Popen(["start", "", path], shell=True)
        self.current_num = 0
        self.path = path

    def start_show(self):
        self._press_key("f5")
        self.current_num = 0


class MacPresentationViewer(PresentationViewer):
    """Viewer for macOS using open command."""

    def open(self, path: str):
        self.close()
        self.process = subprocess.Popen(["open", path])
        self.current_num = 0
        self.path = path


class MacPptxPresentationViewer(MacPresentationViewer):
    """Specialized viewer for pptx files on macOS."""

    def start_show(self):
        time.sleep(5) # Additional sleep time for pptx
        self._press_key("esc")
        self._press_hotkey("command", "option", "p")
        self.current_num = 0


class MacPdfPresentationViewer(MacPresentationViewer):
    """Specialized viewer for pptx files on macOS."""

    def start_show(self):
        self._press_key("return")
        self._press_hotkey("fn", "f")
        time.sleep(1)
        self.current_index = 0


    def goto_slide(self, num: int) -> None:
        """Navigate to a slide using left/right arrows."""

        self._press_hotkey("option", "command", "g")

        for s in str(num):
            self._press_key(s)

        self._press_key("return")
        self.current_num = num


def get_viewer(os_type: str, path: str | None = None) -> PresentationViewer:
    """Return viewer instance depending on OS and file type."""
    if os_type.startswith("win"):
        return WindowsPresentationViewer()
    if os_type == "mac":
        if path and path.lower().endswith(".pptx"):
            return MacPptxPresentationViewer()
        elif path and path.lower().endswith(".pdf"):
            return MacPdfPresentationViewer()
        raise ValueError("Wrong presentation type!")
    return LinuxPresentationViewer()
