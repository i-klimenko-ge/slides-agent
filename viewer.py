import subprocess

class PresentationViewer:
    """Base class for platform specific presentation viewers."""

    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.current_index: int | None = None

    def open(self, path: str):
        raise NotImplementedError

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.process = None
        self.current_index = None

    def goto_slide(self, index: int):
        raise NotImplementedError


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

    def goto_slide(self, index: int):
        if self.process is None:
            return
        steps = index - (self.current_index or 0)
        key = "Right" if steps > 0 else "Left"
        for _ in range(abs(steps)):
            subprocess.run(["xdotool", "key", key], check=False)
        self.current_index = index


class WindowsPresentationViewer(PresentationViewer):
    """Basic viewer for Windows using start command."""

    def open(self, path: str):
        self.close()
        self.process = subprocess.Popen(["start", "", path], shell=True)
        self.current_index = 0

    def goto_slide(self, index: int):
        # Implementation for controlling slides on Windows is platform specific
        # and not provided here.
        self.current_index = index


class MacPresentationViewer(PresentationViewer):
    """Viewer for macOS using open command."""

    def open(self, path: str):
        self.close()
        self.process = subprocess.Popen(["open", path])
        self.current_index = 0

    def goto_slide(self, index: int):
        self.current_index = index


def get_viewer(os_type: str) -> PresentationViewer:
    if os_type.startswith("win"):
        return WindowsPresentationViewer()
    if os_type.startswith("darwin") or os_type == "mac":
        return MacPresentationViewer()
    return LinuxPresentationViewer()
