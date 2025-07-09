from langchain_core.tools import tool
from typing import Annotated
import os
from pptx import Presentation as PresentationFactory
from pptx.presentation import Presentation
from dotenv import load_dotenv

load_dotenv()

PRESENTATIONS_DIR = os.getenv("PRESENTATIONS_DIR", "presentations")

_current_presentation: Presentation | None = None
_current_presentation_path: str | None = None
_current_slide_index: int | None = None

@tool
def open_presentation_tool(query: Annotated[str, "имя файла презентации"]) -> dict:
    """Открыть презентацию для просмотра"""
    global _current_presentation, _current_presentation_path, _current_slide_index

    path = query
    if not os.path.isabs(path):
        path = os.path.join(PRESENTATIONS_DIR, path)

    if not os.path.exists(path):
        return {"status": "error", "message": f"Файл {query} не найден"}

    try:
        prs = PresentationFactory(path)
    except Exception as e:  # pragma: no cover - basic error reporting
        return {"status": "error", "message": f"Не удалось открыть файл: {e}"}

    _current_presentation = prs
    _current_presentation_path = path
    _current_slide_index = 0
    return {
        "status": "ok",
        "slides_count": len(prs.slides),
        "message": f"Открыта презентация {os.path.basename(path)}",
    }

@tool
def close_presentation_tool() -> dict:
    """Завершить просмотр и закрыть презентацию"""
    global _current_presentation, _current_presentation_path, _current_slide_index

    if _current_presentation is None:
        return {"status": "error", "message": "Презентация не открыта"}

    _current_presentation = None
    _current_presentation_path = None
    _current_slide_index = None

    return {"status": "ok", "message": "Презентация закрыта"}

@tool
def open_slide(slide_number: Annotated[int, "номер слайда"]) -> dict:
    """Открыть необходимый слайд в презентации по его номеру"""
    global _current_presentation, _current_slide_index

    if _current_presentation is None:
        return {"status": "error", "message": "Презентация не открыта"}

    prs = _current_presentation

    if slide_number < 1 or slide_number > len(prs.slides):
        return {"status": "error", "message": "Некорректный номер слайда"}

    slide = prs.slides[slide_number - 1]
    _current_slide_index = slide_number - 1
    text = "\n".join(
        shape.text for shape in slide.shapes if hasattr(shape, "text")
    )

    return {"status": "ok", "slide_number": slide_number, "text": text}
