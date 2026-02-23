# Specification - Fix Storage Page ListView Error

## Problem Description
The application throws an error `ListView Control must be added to the page first` when loading the Storage page. This occurs because `self.file_list.update()` is called before the `ListView` has been rendered as part of the page's control tree.

## Proposed Solution
1. Ensure the `view_container` (or its parent) is added to the page before calling `update()` on any of its children.
2. Alternatively, use `page.update()` or ensure the parent container is updated, which recursively updates children if they are already in the tree.
3. In `storage_view.py`, ensure the UI setup is fully committed to the page before performing asynchronous updates that trigger `update()` calls.

## Acceptance Criteria
- Storage page loads without the "ListView Control must be added to the page first" error.
- File list is correctly populated after the page loads.
- Navigation within the storage page (folders, back button) works without errors.