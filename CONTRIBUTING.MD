# Contributing to A-Reliable-Clipboard

Thank you for your interest in contributing to A-Reliable-Clipboard! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- pip

### Setup Development Environment

1. **Fork the repository**

```bash
git clone https://github.com/YOUR_USERNAME/A-Reliable-Clipboard.git
cd A-Reliable-Clipboard
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. **Install development dependencies**

```bash
pip install -e ".[dev]"
```

4. **Verify installation**

```bash
pytest
```

## 🔄 Development Workflow

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions/modifications
- `refactor/` - Code refactoring

### Making Changes

1. Write code following our [coding standards](#coding-standards)
2. Add tests for new functionality
3. Update documentation as needed
4. Run tests and linter
5. Commit your changes

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_storage.py

# Run with coverage
pytest --cov=src/reliable_clipboard --cov-report=html

# Run linter
ruff check src/
```

## 📝 Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line Length**: 100 characters (not 79)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings, single quotes for dict keys
- **Imports**: Grouped and sorted (stdlib, third-party, local)

### Type Hints

Always use type hints for function parameters and return values:

```python
def save_clip(self, content: str, clip_type: str = "text") -> int:
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def search_clips(self, query: str) -> List[Dict[str, Any]]:
    """
    Search for clips containing the query string.
    
    Args:
        query: The string to search for.
        
    Returns:
        List of matching clips.
        
    Raises:
        sqlite3.Error: If database operation fails.
    """
    ...
```

### Error Handling

- Always handle potential exceptions
- Log errors appropriately
- Provide meaningful error messages

```python
try:
    result = some_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

## 🧪 Testing Guidelines

### Test Structure

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names

### Writing Tests

```python
def test_clip_deduplication():
    """Test that consecutive duplicate clips are ignored."""
    history = ClipHistory()
    
    # Add first clip
    clip1 = history.add_clip("test content")
    assert clip1 is not None
    
    # Add duplicate
    clip2 = history.add_clip("test content")
    assert clip2 is None  # Should be ignored
```

### Test Coverage

- Aim for 80%+ code coverage
- Test both success and failure cases
- Test edge cases and boundary conditions
- Mock external dependencies (database, clipboard)

## 💬 Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/modifications
- `refactor`: Code refactoring
- `style`: Code style changes (formatting, etc.)
- `chore`: Maintenance tasks

### Examples

```
feat(storage): add index on timestamp column

Added database index on clips.timestamp to improve query performance
for get_recent_clips() and search operations.

Closes #42
```

```
fix(monitor): handle pyperclip exceptions gracefully

The clipboard monitor now catches PyperclipException and logs errors
instead of crashing the monitoring thread.
```

## 🔍 Pull Request Process

### Before Submitting

1. ✅ All tests pass (`pytest`)
2. ✅ Linter passes (`ruff check src/`)
3. ✅ Code is documented
4. ✅ CHANGELOG updated (if applicable)
5. ✅ README updated (if needed)

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Linter passes
- [ ] All tests pass
```

### Review Process

1. Submit PR with clear description
2. Wait for maintainer review
3. Address feedback
4. Once approved, PR will be merged

### After Merge

- Delete your feature branch
- Pull latest changes from main
- Update your fork

## 🎯 Areas for Contribution

### High Priority

- Encryption for sensitive clipboard data
- System tray integration
- Global hotkey support
- Image clipboard support

### Medium Priority

- Performance optimizations
- Additional storage backends (JSON, MongoDB)
- Export/import functionality
- Cloud sync capabilities

### Good First Issues

Look for issues labeled `good-first-issue` on GitHub.

## 📚 Resources

- [Python PEP 8 Style Guide](https://pep8.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Tkinter Tutorial](https://docs.python.org/3/library/tkinter.html)

## 💡 Questions?

- Open a GitHub Discussion
- Comment on related issues
- Reach out to maintainers

## 🙏 Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort!
