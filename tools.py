"""LangChain tools for listing presentations and controlling slides."""

from langchain_core.tools import tool
from typing import Annotated
import os
import platform
from presentation import create_presentation, BasePresentation
import time

from config import config

PRESENTATIONS_DIR = config.get("presentations_dir", "presentations")
OS_TYPE = config.get("os", platform.system().lower())

_current_presentation: BasePresentation | None = None
_current_presentation_path: str | None = None
_current_slide_num: int | None = None

from viewer import get_viewer


@tool
def list_presentations_tool() -> dict:
    """Получить список файлов презентаций в каталоге."""
    if not os.path.isdir(PRESENTATIONS_DIR):
        return {
            "status": "error",
            "message": f"Каталог {PRESENTATIONS_DIR} не найден"
        }
    files = [
        f for f in os.listdir(PRESENTATIONS_DIR)
        if os.path.isfile(os.path.join(PRESENTATIONS_DIR, f))
        and os.path.splitext(f)[1].lower() in {".pptx", ".pdf"}
    ]
    return {"status": "ok", "files": files}


@tool
def open_presentation_tool(query: Annotated[str, "Имя файла презентации с расширением, например 'презентация 2.pdf'"]) -> dict:
    """Открыть презентацию для просмотра"""
    global _current_presentation, _current_presentation_path, _current_slide_num

    path = query
    if not os.path.isabs(path):
        path = os.path.join(PRESENTATIONS_DIR, path)

    if not os.path.exists(path):
        return {"status": "error", "message": f"Файл {query} не найден"}

    if _current_presentation is not None:
        try:
            _current_presentation.close()
        except Exception:
            pass
        _current_presentation = None
        _current_presentation_path = None
        _current_slide_num = None

    try:
        viewer = get_viewer(OS_TYPE, path)
        prs = create_presentation(path, viewer)
        prs.open()
        time.sleep(2)
        prs.start_show()
    except Exception as e:  # pragma: no cover - basic error reporting
        return {"status": "error", "message": f"Не удалось открыть файл: {e}"}

    _current_presentation = prs
    _current_presentation_path = path
    _current_slide_num = 0
    return {
        "status": "ok",
        "slides_count": prs.slides_count(),
        "presentation_name": os.path.basename(path),
        "message": f"Открыта презентация {os.path.basename(path)}",
    }


@tool
def open_slide(slide_number: Annotated[int, "номер слайда"]) -> dict:
    """Открыть необходимый слайд в презентации по его номеру"""
    global _current_presentation, _current_slide_num

    if _current_presentation is None:
        return {"status": "error", "message": "Презентация не открыта"}

    prs = _current_presentation

    if slide_number < 1 or slide_number > prs.slides_count():
        return {"status": "error", "message": "Некорректный номер слайда"}

    try:
        prs.goto(slide_number)
    except Exception:
        pass

    _current_slide_num = slide_number - 1
    text = prs.get_slide_text(slide_number - 1)

    return {"status": "ok", "slide_number": slide_number, "text": text}


@tool
def next_slide() -> dict:
    """Перейти к следующему слайду текущей презентации."""
    global _current_presentation, _current_slide_num

    if _current_presentation is None or _current_slide_num is None:
        return {"status": "error", "message": "Презентация не открыта"}

    prs = _current_presentation
    if _current_slide_num + 1 >= prs.slides_count():
        return {"status": "error", "message": "Некорректный номер слайда"}

    try:
        prs.next_slide()
    except Exception:
        pass

    _current_slide_num += 1
    text = prs.get_slide_text(_current_slide_num)

    return {
        "status": "ok",
        "slide_number": _current_slide_num + 1,
        "text": text,
    }


@tool
def previous_slide() -> dict:
    """Перейти к предыдущему слайду текущей презентации."""
    global _current_presentation, _current_slide_num

    if _current_presentation is None or _current_slide_num is None:
        return {"status": "error", "message": "Презентация не открыта"}

    prs = _current_presentation
    if _current_slide_num <= 0:
        return {"status": "error", "message": "Некорректный номер слайда"}

    try:
        prs.previous_slide()
    except Exception:
        pass

    _current_slide_num -= 1
    text = prs.get_slide_text(_current_slide_num)

    return {
        "status": "ok",
        "slide_number": _current_slide_num + 1,
        "text": text,
    }


@tool
def list_slides_tool() -> dict:
    """Получить номера слайдов и соответствующее им текстовое содержимое"""
    global _current_presentation

    if _current_presentation is None:
        return {"status": "error", "message": "Презентация не открыта"}

    prs = _current_presentation

    slides = []
    for i in range(prs.slides_count()):
        slides.append({"number": i + 1, "text": prs.get_slide_text(i)})
    return {"status": "ok", "slides": slides}
