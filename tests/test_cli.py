import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from reliable_clipboard.cli import main, DEFAULT_DB_PATH

class TestCLI(unittest.TestCase):

    @patch('reliable_clipboard.cli.StorageManager')
    def test_list_clips(self, mock_storage_cls):
        """Test listing clips."""
        mock_storage = mock_storage_cls.return_value
        mock_storage.get_recent_clips.return_value = [
            {'id': 1, 'content': 'Test content', 'timestamp': 1700000000.0}
        ]

        # Run with list command
        main(['list', '--limit', '5'])

        # Verify storage initialized
        mock_storage_cls.assert_called_with(str(DEFAULT_DB_PATH))
        
        # Verify get_recent_clips called
        mock_storage.get_recent_clips.assert_called_with(limit=5)

    @patch('reliable_clipboard.cli.StorageManager')
    def test_search_clips(self, mock_storage_cls):
        """Test searching clips."""
        mock_storage = mock_storage_cls.return_value
        mock_storage.search_clips.return_value = [
            {'id': 2, 'content': 'Found content', 'timestamp': 1700000100.0}
        ]

        # Run with search command
        main(['search', 'query'])

        # Verify storage initialized
        mock_storage_cls.assert_called_with(str(DEFAULT_DB_PATH))

        # Verify search_clips called
        mock_storage.search_clips.assert_called_with('query')

    @patch('reliable_clipboard.cli.StorageManager')
    @patch('builtins.input', return_value='y')
    def test_clear_history(self, mock_input, mock_storage_cls):
        """Test clearing history."""
        mock_storage = mock_storage_cls.return_value

        # Run with clear command
        main(['clear'])

        # Verify storage initialized
        mock_storage_cls.assert_called_with(str(DEFAULT_DB_PATH))

        # Verify clear_history called
        mock_storage.clear_history.assert_called_once()

    @patch('reliable_clipboard.cli.StorageManager')
    @patch('reliable_clipboard.cli.ClipHistory')
    @patch('reliable_clipboard.cli.ClipboardMonitor')
    @patch('time.sleep', side_effect=KeyboardInterrupt)  # Simulate running loop then interrupt
    def test_start_daemon(self, mock_sleep, mock_monitor_cls, mock_history_cls, mock_storage_cls):
        """Test starting daemon."""
        mock_storage = mock_storage_cls.return_value
        mock_history = mock_history_cls.return_value
        mock_monitor = mock_monitor_cls.return_value

        # Run with start command
        # This will raise KeyboardInterrupt due to side_effect on time.sleep
        # But start_daemon catches it.
        main(['start'])

        # Verify storage initialized
        mock_storage_cls.assert_called_with(str(DEFAULT_DB_PATH))

        # Verify history initialized with storage
        mock_history_cls.assert_called_with(storage_manager=mock_storage)

        # Verify monitor initialized
        mock_monitor_cls.assert_called_once()
        
        # Verify monitor started
        mock_monitor.start.assert_called_once()

        # Verify monitor stopped (in finally block)
        mock_monitor.stop.assert_called_once()

    @patch('reliable_clipboard.cli.StorageManager')
    def test_custom_db_path(self, mock_storage_cls):
        """Test specifying custom DB path."""
        custom_path = "custom.db"
        # Global arguments must come before the subcommand
        main(['--db-path', custom_path, 'list'])
        mock_storage_cls.assert_called_with(custom_path)

if __name__ == '__main__':
    unittest.main()
