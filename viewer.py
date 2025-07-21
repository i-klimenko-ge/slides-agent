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
        # open the file in Keynote and immediately start the slideshow in
        # fullscreen mode. Keynote is bundled with macOS and supports basic
        # AppleScript commands for controlling the presentation. We launch the
        # application and start presenting from the first slide.
        script = ";".join([
            "tell application \"Keynote\"",
            f"open POSIX file \"{path}\"",
            "activate",
            "delay 1",
            "start the front slideshow",
            "end tell",
        ])
        self.process = subprocess.Popen(["osascript", "-e", script])
        self.current_index = 0

    def goto_slide(self, index: int):
        # Use AppleScript to show the given slide in the running slideshow.
        script = (
            'tell application "Keynote" to tell the front document '
            f'to show slide {index + 1}'
        )
        subprocess.run(["osascript", "-e", script], check=False)
        self.current_index = index

    def close(self):
        # Ensure Keynote quits when closing the viewer.
        subprocess.run(["osascript", "-e", 'tell application "Keynote" to quit'], check=False)
        super().close()


def get_viewer(os_type: str) -> PresentationViewer:
    if os_type.startswith("win"):
        return WindowsPresentationViewer()
    if os_type.startswith("darwin") or os_type == "mac":
        return MacPresentationViewer()
    return LinuxPresentationViewer()
