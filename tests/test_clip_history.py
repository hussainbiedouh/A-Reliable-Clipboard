import pytest
from unittest.mock import MagicMock
from reliable_clipboard.clip_history import ClipHistory, Clip
from datetime import datetime

class TestClipHistory:
    
    def test_add_clip_basic(self):
        """Test adding a simple text clip."""
        history = ClipHistory()
        clip = history.add_clip("Test Content")
        
        assert clip is not None
        assert clip.content == "Test Content"
        assert len(history.get_history()) == 1
        assert history.get_latest().content == "Test Content"

    def test_add_clip_deduplication(self):
        """Test that adding the same clip consecutively doesn't duplicate it."""
        history = ClipHistory()
        history.add_clip("Duplicate Me")
        
        # Try adding again
        second_add = history.add_clip("Duplicate Me")
        
        # Should return None and not increase history size
        assert second_add is None
        assert len(history.get_history()) == 1

    def test_add_clip_max_size(self):
        """Test that history respects the max_size limit."""
        max_size = 5
        history = ClipHistory(max_size=max_size)
        
        # Fill up history
        for i in range(max_size + 2):
            history.add_clip(f"Content {i}")
            
        # Should be capped at max_size
        assert len(history.get_history()) == max_size
        
        # Should have discarded the oldest items (0 and 1)
        clips = history.get_history()
        assert clips[0].content == "Content 2"
        assert clips[-1].content == "Content 6"

    def test_clear_history(self):
        """Test clearing the history."""
        history = ClipHistory()
        history.add_clip("Delete Me")
        assert len(history.get_history()) == 1
        
        history.clear()
        assert len(history.get_history()) == 0
        assert history.get_latest() is None

    def test_immutability_of_get_history(self):
        """Ensure get_history returns a copy, not the internal list."""
        history = ClipHistory()
        history.add_clip("Original")
        
        external_list = history.get_history()
        external_list.append(Clip("Hacked"))
        
        assert len(history.get_history()) == 1
        assert history.get_latest().content == "Original"

    def test_add_empty_clip(self):
        """Test that empty clips are ignored."""
        history = ClipHistory()
        clip = history.add_clip("")
        assert clip is None
        assert len(history.get_history()) == 0

    def test_storage_integration(self):
        """Test that ClipHistory uses storage if provided."""
        mock_storage = MagicMock()
        mock_storage.save_clip.return_value = 123
        mock_storage.get_recent_clips.return_value = []
        
        history = ClipHistory(storage_manager=mock_storage)
        
        # Test add_clip calls save_clip
        clip = history.add_clip("Persisted Clip")
        assert clip is not None
        assert clip.content == "Persisted Clip"
        
        # Verify save_clip called
        mock_storage.save_clip.assert_called_once_with("Persisted Clip", "text")
        
        # Verify clip ID set (Clip dataclass updated to have id)
        assert clip.id == 123
        
        # Test clear calls clear_history
        history.clear()
        mock_storage.clear_history.assert_called_once()
