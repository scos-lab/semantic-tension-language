# Contributing to STL Parser

Thank you for your interest in contributing to the STL Parser project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Familiarity with STL specification (see [docs](../spec/))

### Setup Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/semantic-tension-language.git
   cd semantic-tension-language/parser
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

4. **Verify Setup**
   ```bash
   pytest
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 2. Make Changes

- Write clean, readable code
- Follow coding standards (see below)
- Add/update tests for your changes
- Update documentation as needed

### 3. Run Tests and Linters

```bash
# Format code
black stl_parser/ tests/

# Lint code
ruff stl_parser/ tests/

# Type check
mypy stl_parser/

# Run tests
pytest

# Check coverage
pytest --cov=stl_parser --cov-report=html
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: Add new feature description"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python Style

- **PEP 8** compliance (enforced by black and ruff)
- **Line length**: 100 characters maximum
- **Type hints**: All functions must have type annotations
- **Docstrings**: All public functions/classes must have docstrings

### Example

```python
from typing import List, Optional
from pydantic import BaseModel


class Statement(BaseModel):
    """Represents an STL statement.

    Args:
        source: Source anchor
        target: Target anchor
        modifiers: Optional modifiers

    Raises:
        ValueError: If anchors are invalid
    """

    source: str
    target: str
    modifiers: Optional[dict] = None

    def validate(self) -> bool:
        """Validate the statement.

        Returns:
            True if valid, False otherwise
        """
        return self.source and self.target
```

### Docstring Format

Use Google-style docstrings:

```python
def parse(text: str, mode: str = "strict") -> ParseResult:
    """Parse STL text into structured format.

    Args:
        text: STL text to parse
        mode: Validation mode ("strict", "lenient", or "validation")

    Returns:
        ParseResult containing statements and any errors

    Raises:
        ValueError: If mode is invalid
        ParseError: If text cannot be parsed

    Example:
        >>> parser = STLParser()
        >>> result = parser.parse("[A] → [B]")
        >>> result.is_valid
        True
    """
    pass
```

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_parser.py           # Parser tests
├── test_validator.py        # Validator tests
├── test_serializer.py       # Serializer tests
├── test_roundtrip.py        # Round-trip tests
└── fixtures/
    ├── valid/               # Valid STL examples
    ├── invalid/             # Invalid STL examples
    └── edge_cases/          # Edge case examples
```

### Writing Tests

```python
import pytest
from stl_parser import STLParser, ParseError


class TestParser:
    """Test suite for parser functionality."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return STLParser()

    def test_simple_statement(self, parser):
        """Test parsing simple statement."""
        result = parser.parse("[A] → [B]")
        assert result.is_valid
        assert len(result.statements) == 1

    def test_invalid_anchor(self, parser):
        """Test error on invalid anchor."""
        result = parser.parse("[Invalid!]")
        assert not result.is_valid
        assert result.errors[0].code == "E001"

    @pytest.mark.parametrize("input,expected", [
        ("[A] → [B]", True),
        ("[A] [B]", False),
        ("[A] → [B] → [C]", True),
    ])
    def test_multiple_cases(self, parser, input, expected):
        """Test multiple input cases."""
        result = parser.parse(input)
        assert result.is_valid == expected
```

### Test Coverage

- **Minimum coverage**: 90%
- **Critical paths**: 100% coverage
- **Edge cases**: Must be tested
- **Error paths**: Must be tested

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::TestParser::test_simple_statement

# Run with coverage
pytest --cov=stl_parser --cov-report=html

# Run only fast tests
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build process or tooling changes

### Examples

```bash
# Feature
git commit -m "feat(parser): Add support for chained paths"

# Bug fix
git commit -m "fix(validator): Correct confidence range validation"

# Documentation
git commit -m "docs: Update README with new examples"

# Multiple paragraphs
git commit -m "feat(serializer): Add RDF/Turtle export

Implements RDF serialization according to spec Section 6.
Uses rdflib for robust RDF generation.

Closes #123"
```

### Commit Best Practices

- **Atomic commits**: One logical change per commit
- **Clear messages**: Explain what and why, not how
- **Reference issues**: Use `Closes #123` or `Fixes #456`
- **Keep it small**: Prefer many small commits over large ones

## Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Code coverage ≥ 90%
3. ✅ Linters pass (black, ruff, mypy)
4. ✅ Documentation updated
5. ✅ CHANGELOG updated (if applicable)
6. ✅ Commits follow guidelines

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review performed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] No new warnings generated

## Related Issues
Closes #(issue number)
```

### Review Process

1. **Automated checks**: CI must pass
2. **Code review**: At least one approval required
3. **Discussion**: Address all review comments
4. **Updates**: Push fixes to same branch
5. **Merge**: Squash and merge when approved

## Reporting Issues

### Before Reporting

1. **Search existing issues**: Avoid duplicates
2. **Check documentation**: Issue might be explained
3. **Try latest version**: Bug might be fixed

### Issue Template

```markdown
## Description
Clear description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Windows 11, Ubuntu 22.04]
- Python version: [e.g., 3.11.2]
- STL Parser version: [e.g., 1.0.0]

## Additional Context
Any other relevant information
```

### Issue Types

- **Bug Report**: Something isn't working
- **Feature Request**: Suggest new functionality
- **Documentation**: Improve or add documentation
- **Question**: Ask for help or clarification

## Development Tips

### Debugging

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use ipdb for debugging
import ipdb; ipdb.set_trace()
```

### Performance Testing

```python
import time
from stl_parser import STLParser

parser = STLParser()
start = time.time()
result = parser.parse(large_stl_text)
elapsed = time.time() - start
print(f"Parsed in {elapsed:.2f}s")
```

### Testing with Real Data

```bash
# Create test fixtures
mkdir -p tests/fixtures/valid
echo "[A] → [B]" > tests/fixtures/valid/simple.stl

# Run parser on fixture
stl validate tests/fixtures/valid/simple.stl
```

## Resources

- [STL Specification](../spec/stl-core-spec-v1.0.md)
- [Implementation Plan](../../STL_Parser_Implementation_Plan.md)
- [Lark Parser Documentation](https://lark-parser.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)

## Questions?

- **GitHub Discussions**: For questions and discussions
- **GitHub Issues**: For bug reports and feature requests
- **Email**: contact@scos-lab.org

---

Thank you for contributing to STL Parser! 🎉
