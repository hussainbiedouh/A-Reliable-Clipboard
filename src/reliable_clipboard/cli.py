import argparse
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from .storage import StorageManager
from .clipboard_monitor import ClipboardMonitor
from .clip_history import ClipHistory
from .gui import start_gui

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path.home() / ".reliable_clipboard.db"

def format_timestamp(ts: float) -> str:
    """Formats a unix timestamp to a readable string."""
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def print_clips(clips: List[Dict[str, Any]]):
    """Prints a list of clips in a table format."""
    if not clips:
        print("No clips found.")
        return

    # specific format for alignment
    print(f"{'ID':<5} | {'Type':<8} | {'Timestamp':<20} | {'Content (Snippet)'}")
    print("-" * 80)
    for clip in clips:
        content = clip['content'].replace('\n', ' ')
        clip_type = clip.get('clip_type', 'text')
        
        if clip_type == 'image':
            content = "[IMAGE]"
        elif clip_type == 'file':
            files = content.split('\n')
            content = f"[FILE{'S' if len(files) > 1 else ''}]: {len(files)} item{'s' if len(files) > 1 else ''}"
        else:
            if len(content) > 40:
                content = content[:37] + "..."
                
        print(f"{clip['id']:<5} | {clip_type:<8} | {format_timestamp(clip['timestamp']):<20} | {content}")

def start_daemon(args):
    """Starts the clipboard monitor daemon."""
    db_path = args.db_path
    print(f"Starting reliable-clipboard daemon...")
    print(f"Database: {db_path}")
    print("Press Ctrl+C to stop.")

    try:
        storage = StorageManager(str(db_path))
        history = ClipHistory(storage_manager=storage)
        
    # Define callback to add clip to history
        def on_clip_change(content, clip_type):
            try:
                clip = history.add_clip(content, clip_type)
                if clip and clip.id:
                    type_str = f" ({clip_type})" if clip_type != "text" else ""
                    print(f"[{format_timestamp(time.time())}] Captured new clip (ID: {clip.id}){type_str}")
            except Exception as e:
                logger.error(f"Error processing clip: {e}")

        monitor = ClipboardMonitor(on_change=on_clip_change)
        monitor.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping daemon...")
    except Exception as e:
        logger.error(f"Daemon failed: {e}")
        sys.exit(1)
    finally:
        if 'monitor' in locals():
            monitor.stop()

def list_clips(args):
    """Lists recent clips."""
    try:
        storage = StorageManager(str(args.db_path))
        clips = storage.get_recent_clips(limit=args.limit)
        print_clips(clips)
    except Exception as e:
        logger.error(f"Error listing clips: {e}")
        sys.exit(1)

def search_clips(args):
    """Searches for clips."""
    try:
        storage = StorageManager(str(args.db_path))
        clips = storage.search_clips(args.query)
        print_clips(clips)
    except Exception as e:
        logger.error(f"Error searching clips: {e}")
        sys.exit(1)

def clear_history(args):
    """Clears all clips."""
    try:
        storage = StorageManager(str(args.db_path))
        confirm = input("Are you sure you want to clear all history? [y/N] ")
        if confirm.lower() == 'y':
            storage.clear_history()
            print("History cleared.")
        else:
            print("Operation cancelled.")
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        sys.exit(1)

def main(args=None):
    parser = argparse.ArgumentParser(description="A Reliable Clipboard Manager")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Path to the database file")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Start command
    parser_start = subparsers.add_parser("start", help="Start the clipboard monitor daemon")
    parser_start.set_defaults(func=start_daemon)

    # List command
    parser_list = subparsers.add_parser("list", help="List recent clips")
    parser_list.add_argument("-n", "--limit", type=int, default=10, help="Number of clips to show")
    parser_list.set_defaults(func=list_clips)

    # Search command
    parser_search = subparsers.add_parser("search", help="Search clips")
    parser_search.add_argument("query", type=str, help="Search query")
    parser_search.set_defaults(func=search_clips)

    # Clear command
    parser_clear = subparsers.add_parser("clear", help="Clear history")
    parser_clear.set_defaults(func=clear_history)

    # GUI command
    parser_gui = subparsers.add_parser("gui", help="Start the graphical user interface")
    parser_gui.set_defaults(func=lambda args: start_gui(str(args.db_path)))

    args = parser.parse_args(args)
    
    # If no command specified, launch GUI by default
    if not args.command:
        start_gui(str(args.db_path))
    elif hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
