"""
Build script for creating Windows executable using PyInstaller.
"""
import PyInstaller.__main__
import sys
from pathlib import Path

def build_exe():
    """Build the executable for A-Reliable-Clipboard."""
    
    # Get project root
    project_root = Path(__file__).parent
    src_path = project_root / "src" / "reliable_clipboard"
    
    # PyInstaller arguments
    args = [
        str(src_path / "cli.py"),  # Entry point
        "--name=reliable-clipboard",
        "--onefile",  # Single executable
        "--windowed",  # No console window for GUI
        "--icon=NONE",  # No icon for now
        f"--add-data={src_path / '__init__.py'};reliable_clipboard",
        f"--add-data={src_path / 'clip_history.py'};reliable_clipboard",
        f"--add-data={src_path / 'clipboard_monitor.py'};reliable_clipboard",
        f"--add-data={src_path / 'storage.py'};reliable_clipboard",
        f"--add-data={src_path / 'gui.py'};reliable_clipboard",
        "--hidden-import=reliable_clipboard",
        "--hidden-import=reliable_clipboard.clip_history",
        "--hidden-import=reliable_clipboard.clipboard_monitor",
        "--hidden-import=reliable_clipboard.storage",
        "--hidden-import=reliable_clipboard.gui",
        "--clean",
        "--noconfirm",
    ]
    
    print("🔨 Building executable with PyInstaller...")
    print(f"📁 Source path: {src_path}")
    print("⚙️  Configuration: Single file, windowed mode")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✅ Build complete!")
        print(f"📦 Executable location: {project_root / 'dist' / 'reliable-clipboard.exe'}")
        return 0
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(build_exe())
