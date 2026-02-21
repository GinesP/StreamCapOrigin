import flet as ft
from .logger import logger

def safe_update(control):
    """Safely update a Flet control only if it's attached to a page."""
    if not control:
        return
    try:
        if hasattr(control, "page") and control.page:
            control.update()
        elif isinstance(control, ft.Page):
            control.update()
    except (AssertionError, Exception) as e:
        logger.debug(f"Safe update failed for {type(control).__name__}: {e}")

def is_page_active(app, page_obj):
    """Check if the given page is the currently active page in the app."""
    return app.current_page == page_obj
