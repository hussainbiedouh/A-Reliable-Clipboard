# A-Reliable-Clipboard 📋

A robust, cross-platform clipboard manager built with Python that monitors clipboard changes in real-time, maintains history with persistent storage, and provides both CLI and GUI interfaces.

## ✨ Features

- ⚡ **Real-time Clipboard Monitoring**: Automatically captures everything you copy
- 💾 **Persistent History**: SQLite-backed storage that survives restarts
- 🔍 **Searchable History**: Quickly find past clips with full-text search
- 🖥️ **Command-Line Interface**: Powerful CLI for terminal users
- 🎨 **Graphical Interface**: User-friendly desktop application with Tkinter
- 🔄 **Deduplication**: Automatically ignores consecutive duplicate clips
- 🧪 **Well-Tested**: Comprehensive test suite with 23+ passing tests

## 📦 Installation

### From Source

```bash
git clone https://github.com/yourusername/A-Reliable-Clipboard.git
cd A-Reliable-Clipboard
pip install -e .
```

### Requirements

- Python 3.10+
- Dependencies: `pyperclip`, `watchdog`
- Dev dependencies: `pytest`, `ruff`

## 🚀 Usage

### Command-Line Interface

#### Start the Clipboard Monitor

```bash
reliable-clip start
```

This starts a background daemon that monitors your clipboard and saves all clips to the database.

#### List Recent Clips

```bash
# Show last 10 clips
reliable-clip list

# Show last 20 clips
reliable-clip list -n 20
```

#### Search Clips

```bash
reliable-clip search "password"
```

#### Clear History

```bash
reliable-clip clear
```

#### Custom Database Location

```bash
reliable-clip --db-path /path/to/custom.db start
```

### Graphical User Interface

```bash
reliable-clip gui
```

The GUI provides:
- 📋 **Clip List**: View all your clipboard history
- 🔍 **Search Bar**: Filter clips in real-time
- 📋 **Copy Button**: Restore any clip to your clipboard
- 🗑️ **Delete Button**: Remove unwanted clips
- ⚡ **Monitor Toggle**: Start/stop clipboard monitoring from the GUI
- 🔄 **Auto-Refresh**: Automatically updates when new clips are captured

### Python API

```python
from reliable_clipboard import ClipboardMonitor, ClipHistory, StorageManager

# Create storage manager
storage = StorageManager("~/.reliable_clipboard.db")

# Create history manager
history = ClipHistory(storage_manager=storage)

# Define callback for clipboard changes
def on_clip_change(content):
    clip = history.add_clip(content)
    if clip:
        print(f"Captured: {content[:50]}...")

# Start monitoring
monitor = ClipboardMonitor(on_change=on_clip_change)
monitor.start()

# Keep running...
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    monitor.stop()
```

## 🏗️ Architecture

```
src/reliable_clipboard/
├── clip_history.py          # In-memory clip management with deduplication
├── clipboard_monitor.py     # Background clipboard monitoring thread
├── storage.py               # SQLite persistence layer
├── cli.py                   # Command-line interface
└── gui.py                   # Tkinter GUI application
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/reliable_clipboard

# Run specific test file
pytest tests/test_storage.py
```

## 🛠️ Development

See [PLAN.MD](PLAN.MD) for the complete development roadmap.

### Setup Development Environment

```bash
# Clone and install in editable mode
git clone https://github.com/yourusername/A-Reliable-Clipboard.git
cd A-Reliable-Clipboard
pip install -e ".[dev]"

# Run linter
ruff check src/

# Run tests
pytest
```

### Project Structure

- `src/reliable_clipboard/`: Main source code
- `tests/`: Test suite
- `docs/`: Documentation (coming soon)
- `pyproject.toml`: Project configuration and dependencies
- `PLAN.MD`: Development roadmap

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.MD](CONTRIBUTING.MD) for guidelines.

## 🔮 Roadmap

- [x] Core clipboard monitoring
- [x] SQLite persistence
- [x] CLI interface
- [x] GUI interface
- [ ] Encryption for sensitive data
- [ ] System tray integration
- [ ] Global hotkeys
- [ ] Image clipboard support
- [ ] Cloud sync (optional)

## 📊 Status

**Current Version**: 0.1.0 (Alpha)

- ✅ Stages 1-5 Complete
- 🚧 Stage 6 (Polish & Packaging) In Progress

## 🐛 Known Issues

- GUI tests require isolation due to tkinter initialization
- System tray icon not yet implemented
- Global hotkeys pending

## 💬 Support

For issues and questions, please open a GitHub issue.

## 👏 Acknowledgments

Built with:
- [pyperclip](https://github.com/asweigart/pyperclip) - Cross-platform clipboard access
- [watchdog](https://github.com/gorakhargosh/watchdog) - File system monitoring
- [pytest](https://pytest.org/) - Testing framework
