import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .storage import StorageManager

@dataclass
class Clip:
    """Represents a clipboard entry."""
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    clip_type: str = "text"
    id: Optional[int] = None

class ClipHistory:
    """Manages the history of clipboard entries."""
    
    def __init__(self, max_size: int = 100, storage_manager: Optional['StorageManager'] = None):
        self._history: List[Clip] = []
        self._max_size = max_size
        self._storage = storage_manager
        self._logger = logging.getLogger(__name__)

    def add_clip(self, content: str, clip_type: str = "text") -> Optional[Clip]:
        """Adds a new clip to the history, respecting deduplication."""
        if not content:
            return None
            
        # Deduplication: check if same as last clip (content and type)
        if self._history and self._history[-1].content == content and self._history[-1].clip_type == clip_type:
            return None
            
        clip = Clip(content=content, clip_type=clip_type)
        
        if self._storage:
            try:
                # Save to storage
                clip.id = self._storage.save_clip(content, clip.clip_type)
            except Exception as e:
                self._logger.error(f"Failed to save clip to storage: {e}")
                
        self._history.append(clip)
        
        # Maintain size limit
        if len(self._history) > self._max_size:
            self._history.pop(0)
            
        self._logger.debug(f"Added new clip (type: {clip_type}): {content[:20]}...")
        return clip

    def get_history(self) -> List[Clip]:
        """Returns a copy of the clip history."""
        return self._history.copy()

    def clear(self):
        """Clears the history."""
        self._history.clear()
        if self._storage:
            try:
                self._storage.clear_history()
            except Exception as e:
                self._logger.error(f"Failed to clear storage history: {e}")
        
    def get_latest(self) -> Optional[Clip]:
        """Returns the most recent clip."""
        return self._history[-1] if self._history else None
