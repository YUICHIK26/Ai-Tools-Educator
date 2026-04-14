# Contributing to AI Tools Educator

Thank you for your interest in contributing to the AI Tools Educator project! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Style Guide](#style-guide)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

Please be respectful and constructive in all interactions. We're committed to providing a welcoming and inclusive environment for everyone.

## Getting Started

### Prerequisites
- Python 3.10.11 or higher
- Git
- A GitHub account
- Basic understanding of Flask and Python

### Fork & Clone
1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Ai-Tools-Educator.git
   cd Ai-Tools-Educator
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/YUICHIK26/Ai-Tools-Educator.git
   ```

## Development Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r Requirements.txt
```

### 3. Setup Environment Variables
```bash
cp .env.example .env
# Edit .env with your development API keys
```

### 4. Verify Installation
```bash
cd app
python app.py
# Visit http://localhost:5000
```

## Making Changes

### Branch Naming
- Feature: `feature/description-of-feature`
- Bug fix: `bugfix/description-of-bug`
- Documentation: `docs/description-of-docs`

Example:
```bash
git checkout -b feature/add-new-ai-tool-category
```

### Code Changes
1. Make your changes in the appropriate files
2. Test locally:
   ```bash
   python app.py
   ```
3. Run any existing tests:
   ```bash
   python -m pytest  # If tests exist
   ```

### Commit Messages
Use clear, descriptive commit messages:
```
feat: Add new AI tool category for music generation
fix: Resolve chatbot response timeout issue
docs: Update API setup instructions
refactor: Simplify Model.py decision routing
```

Format:
```
<type>: <subject>

<body (optional)>
<footer (optional)>
```

Types: `feat`, `fix`, `docs`, `refactor`, `style`, `test`, `chore`

## Submitting Changes

### Before Creating PR
```bash
# Update your main branch
git fetch upstream
git checkout main
git merge upstream/main

# Rebase your feature branch
git checkout your-feature-branch
git rebase main
```

### Create Pull Request
1. Push your branch to your fork:
   ```bash
   git push origin your-feature-branch
   ```
2. Go to GitHub and create a Pull Request
3. Fill in the PR template with:
   - Description of changes
   - Related issues (if any)
   - Screenshots/videos (if applicable)
   - Testing checklist

### PR Title Format
```
[CATEGORY] Brief description of changes
```

Examples:
- `[Feature] Add support for multiple conversation themes`
- `[Fix] Resolve Firebase authentication timeout`
- `[Docs] Update README with new setup instructions`

### PR Checklist
- [ ] Code follows project style guide
- [ ] Tested locally
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No sensitive data (API keys, passwords) committed
- [ ] `.env` is not committed (only `.env.example`)

## Style Guide

### Python Code
- Follow PEP 8 conventions
- Use meaningful variable names
- Add docstrings to functions:
  ```python
  def analyze_screen():
      """Analyze current screen content and return insights.
      
      Returns:
          dict: Screen analysis results with identified text and objects
      """
      pass
  ```
- Comment complex logic
- Aim for <100 lines per function

### JavaScript/HTML
- Use semantic HTML5
- Comment non-obvious code
- Use consistent indentation
- Follow camelCase for JS variables

### File Structure
```
backend_module/
├── __init__.py
├── main.py          # Core functionality
├── utils.py         # Helper functions
└── config.py        # Configuration
```

## Areas for Contribution

### High Priority
- [ ] Performance optimizations
- [ ] Error handling improvements
- [ ] API integration stability
- [ ] Testing coverage

### Medium Priority
- [ ] New AI tool categories
- [ ] UI/UX improvements
- [ ] Documentation enhancements
- [ ] Additional language support

### Low Priority
- [ ] Theme customizations
- [ ] Minor UI tweaks
- [ ] Documentation typos

## Reporting Issues

### Before Reporting
1. Check existing issues for duplicates
2. Test on the latest `main` branch
3. Check documentation and README
4. Verify it's not a setup issue

### Creating Issue
Include:
1. **Clear title**: "Module X not working" → "Chatbot fails with Groq API timeout"
2. **Description**: What you expected vs. what happened
3. **Reproduction steps**:
   ```
   1. Start the app
   2. Go to chat page
   3. Send a long message
   ```
4. **Environment**:
   ```
   Python: 3.10.11
   OS: Windows 11
   Branch: main
   ```
5. **Error message/Logs**:
   ```
   Traceback (most recent call last):
     File "app.py", line XX, in function_name
   ```
6. **Screenshots** (if applicable)

## Testing

### Running Tests (when added)
```bash
python -m pytest tests/
python -m pytest tests/test_chatbot.py -v
```

### Manual Testing Checklist
- [ ] Web app loads
- [ ] Chat functionality works
- [ ] All pages load without errors
- [ ] Firebase auth works
- [ ] Text-to-speech doesn't crash
- [ ] No API errors in console

## Documentation

If you add features, update:
- `README.md` - Add feature to overview
- `.env.example` - Add new config variables
- Inline code comments - For complex logic
- CONTRIBUTING.md - If adding new contribution areas

## Questions?

- Open a GitHub Discussion
- Check existing issues
- Email through the contact page in the app

## Recognition

Contributors will be:
- Added to Contributors list in README
- Thanked in release notes
- Referenced in commit history

Thank you for contributing! 🎉

---

**Happy coding!** 🚀
