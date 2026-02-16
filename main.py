#!/usr/bin/env python3
"""
Standalone entry point for A-Reliable-Clipboard.
This file uses absolute imports to work with PyInstaller.
If no command is specified, it launches the GUI by default.
"""
import sys
import os

# Set up path for both development and frozen executable
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    app_path = sys._MEIPASS
    sys.path.insert(0, app_path)
else:
    # Running in normal Python environment
    app_path = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(app_path, 'src')
    if os.path.exists(src_path):
        sys.path.insert(0, src_path)

# Now we can import normally
if __name__ == "__main__":
    from reliable_clipboard.cli import main
    
    # If no command is specified, default to GUI
    if len(sys.argv) == 1:
        print("No command specified. Launching GUI...")
        sys.argv.append('gui')
    
    main()
