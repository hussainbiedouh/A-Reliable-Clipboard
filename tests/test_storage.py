import pytest
import sqlite3
import os
import time
from reliable_clipboard.storage import StorageManager

@pytest.fixture
def storage_manager(tmp_path):
    """Fixture to provide a clean StorageManager instance."""
    db_file = tmp_path / "test_clips.db"
    return StorageManager(str(db_file))

def test_init_creates_table(storage_manager):
    """Test that initializing StorageManager creates the table."""
    conn = sqlite3.connect(storage_manager.db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clips';")
    result = cursor.fetchone()
    conn.close()
    assert result is not None
    assert result[0] == 'clips'

def test_save_clip(storage_manager):
    """Test saving a clip."""
    clip_id = storage_manager.save_clip("Test Content", "text")
    assert isinstance(clip_id, int)
    
    # Verify directly in DB
    conn = sqlite3.connect(storage_manager.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM clips WHERE id=?", (clip_id,))
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    assert row['content'] == "Test Content"
    assert row['clip_type'] == "text"
    assert isinstance(row['timestamp'], float)

def test_save_clip_empty_content(storage_manager):
    """Test saving empty content raises ValueError."""
    with pytest.raises(ValueError):
        storage_manager.save_clip("")

def test_get_recent_clips(storage_manager):
    """Test retrieving recent clips."""
    storage_manager.save_clip("Clip 1")
    time.sleep(0.1) # Ensure timestamp difference
    storage_manager.save_clip("Clip 2")
    time.sleep(0.1)
    storage_manager.save_clip("Clip 3")
    
    clips = storage_manager.get_recent_clips(limit=2)
    assert len(clips) == 2
    assert clips[0]['content'] == "Clip 3" # Most recent first
    assert clips[1]['content'] == "Clip 2"

def test_search_clips(storage_manager):
    """Test searching for clips."""
    storage_manager.save_clip("Hello World")
    storage_manager.save_clip("Goodbye World")
    storage_manager.save_clip("Hello Python")
    
    results = storage_manager.search_clips("Hello")
    assert len(results) == 2
    contents = [c['content'] for c in results]
    assert "Hello World" in contents
    assert "Hello Python" in contents
    assert "Goodbye World" not in contents

def test_delete_clip(storage_manager):
    """Test deleting a clip."""
    id1 = storage_manager.save_clip("Clip 1")
    id2 = storage_manager.save_clip("Clip 2")
    
    assert storage_manager.delete_clip(id1) is True
    
    clips = storage_manager.get_recent_clips()
    assert len(clips) == 1
    assert clips[0]['content'] == "Clip 2"
    
    # Try deleting non-existent clip
    assert storage_manager.delete_clip(999) is False

def test_clear_history(storage_manager):
    """Test clearing all history."""
    storage_manager.save_clip("Clip 1")
    storage_manager.save_clip("Clip 2")
    
    storage_manager.clear_history()
    
    clips = storage_manager.get_recent_clips()
    assert len(clips) == 0
