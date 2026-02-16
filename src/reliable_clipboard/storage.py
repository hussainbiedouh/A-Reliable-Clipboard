import sqlite3
import logging
import time
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages SQLite storage for clipboard clips."""

    def __init__(self, db_path: str):
        """
        Initialize the storage manager.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._create_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        return conn

    def _create_table(self):
        """Creates the clips table and indexes if they don't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL,
            clip_type TEXT DEFAULT 'text'
        );
        """
        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_clips_timestamp ON clips(timestamp DESC);
        """
        create_type_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_clips_type ON clips(clip_type);
        """
        try:
            with self._get_connection() as conn:
                conn.execute(create_table_sql)
                conn.execute(create_index_sql)
                conn.execute(create_type_index_sql)
        except sqlite3.Error as e:
            logger.error(f"Failed to create table: {e}")
            raise

    def save_clip(self, content: str, clip_type: str = "text") -> int:
        """
        Save a new clip to the database.
        
        Args:
            content: The content of the clip. For images, this should be base64 encoded.
            clip_type: Type of the clip (default 'text', or 'image', 'file').
            
        Returns:
            The ID of the newly inserted clip.
            
        Raises:
            sqlite3.Error: If database operation fails.
        """
        if not content:
            raise ValueError("Content cannot be empty")

        timestamp = time.time()
        sql = "INSERT INTO clips (content, timestamp, clip_type) VALUES (?, ?, ?)"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (content, timestamp, clip_type))
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Failed to save clip: {e}")
            raise

    def get_recent_clips(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent clips.
        
        Args:
            limit: Maximum number of clips to return.
            
        Returns:
            List of dictionaries representing clips.
        """
        sql = "SELECT * FROM clips ORDER BY timestamp DESC LIMIT ?"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get recent clips: {e}")
            return []

    def search_clips(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for clips containing the query string.
        
        Args:
            query: The string to search for.
            
        Returns:
            List of matching clips.
        """
        sql = "SELECT * FROM clips WHERE content LIKE ? ORDER BY timestamp DESC"
        wildcard_query = f"%{query}%"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (wildcard_query,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to search clips: {e}")
            return []

    def delete_clip(self, clip_id: int) -> bool:
        """
        Delete a clip by its ID.
        
        Args:
            clip_id: The ID of the clip to delete.
            
        Returns:
            True if deleted, False otherwise.
        """
        sql = "DELETE FROM clips WHERE id = ?"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (clip_id,))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to delete clip {clip_id}: {e}")
            return False

    def clear_history(self):
        """Delete all clips from history."""
        sql = "DELETE FROM clips"
        
        try:
            with self._get_connection() as conn:
                conn.execute(sql)
        except sqlite3.Error as e:
            logger.error(f"Failed to clear history: {e}")
            raise
