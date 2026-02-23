import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import flet as ft
from app.ui.views.storage_view import StoragePage

@pytest.mark.asyncio
async def test_storage_page_load_no_longer_triggers_listview_error():
    # Mock app and its components
    mock_app = MagicMock()
    mock_app.page = MagicMock(spec=ft.Page)
    
    mock_app.settings = MagicMock()
    mock_app.settings.get_video_save_path.return_value = "/mock/path"
    
    # Mock language data
    mock_app.language_manager = MagicMock()
    mock_app.language_manager.language = {
        "storage_page": {
            "storage_path": "Storage Path",
            "current_path": "Current Path",
            "empty_recording_folder": "Empty Recording Folder",
            "go_back": "Go Back",
            "file_list_update_error": "Error updating file list",
            "current_path": "Current Path"
        },
        "base": {
            "confirm": "Confirm"
        }
    }
    
    mock_app.is_mobile = False
    
    # Instantiate StoragePage
    page = StoragePage(mock_app)
    
    # Set current_page to self so is_page_active returns True
    mock_app.current_page = page
    
    # Mock os.path.exists and os.scandir to avoid real FS calls
    with patch("os.path.exists", return_value=True), \
         patch("os.scandir", return_value=MagicMock()):
        
        # This should now complete without raising "Control must be added to the page first"
        # because we use safe_update()
        await page.load()

    assert page.file_list.page is None # Still none, but no error
