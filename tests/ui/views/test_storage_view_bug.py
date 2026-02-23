import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import flet as ft
from app.ui.views.storage_view import StoragePage

@pytest.mark.asyncio
async def test_storage_page_load_triggers_listview_error():
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
    
    # We want to catch the error when self.file_list.update() is called
    # In StoragePage.load(), it calls setup_ui() then update_file_list()
    # update_file_list() calls self.file_list.update()
    
    # Mock os.path.exists and os.scandir to avoid real FS calls
    with patch("os.path.exists", return_value=True), \
         patch("os.scandir", return_value=MagicMock()):
        
        try:
            await page.load()
        except Exception as e:
            print(f"Caught exception: {e}")
            # Flet's .update() raises an Exception if the control is not on a page.
            assert "Control must be added to the page first" in str(e)
            return

    pytest.fail("Did not raise 'Control must be added to the page first'")
