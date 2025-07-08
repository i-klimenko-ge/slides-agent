from langchain_core.tools import tool
from typing import List, Annotated

@tool
def open_presentation_tool(query: Annotated[str, "имя файла презентации"]) -> dict:
    """Открыть презентацию для просмотра"""
    pass

@tool
def close_presentation_tool() -> dict:
    """Завершить просмотр и закрыть презентацию"""
    pass

@tool
def open_slide(answer: Annotated[str, "запрос для поиска"]) -> dict:
    """Открыть необходимый слайд в презентации"""
    pass
