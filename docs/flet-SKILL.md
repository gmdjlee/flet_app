---
name: flet-feature-planner
description: Creates phase-based feature plans for Python Flet 0.8+ cross-platform applications with quality gates and incremental delivery structure. Use when planning Flet features, organizing work, breaking down UI tasks, creating cross-platform roadmaps, or structuring Flet development strategy. Keywords: flet, plan, planning, phases, breakdown, strategy, roadmap, organize, structure, outline, cross-platform, python, desktop, mobile, web.
---

# Flet Feature Planner

## Purpose
Generate structured, phase-based plans for Flet cross-platform applications where:
- Each phase delivers complete, runnable functionality across target platforms
- Quality gates enforce validation before proceeding
- User approves plan before any work begins
- Progress tracked via markdown checkboxes
- Each phase is 1-4 hours maximum
- Platform-specific considerations documented

## Flet Overview

### What is Flet?
Flet is a Python framework for building real-time web, mobile and desktop applications using Flutter as the rendering engine. Version 0.8+ provides:
- Cross-platform support: Windows, macOS, Linux, iOS, Android, Web
- Material Design 3 and Cupertino widgets
- Hot reload for rapid development
- Python-native syntax with imperative UI programming model

### Documentation References
- **Introduction & Tutorials**: https://docs.flet.dev/
- **API Reference (Controls/Services)**: https://docs.flet.dev/api-reference/
- **Cookbook (Best Practices)**: https://docs.flet.dev/cookbook/
- **Publishing Guide**: https://docs.flet.dev/publish/

## Planning Workflow

### Step 1: Requirements Analysis
1. Read relevant files to understand existing codebase architecture
2. Identify target platforms (desktop/mobile/web)
3. Review Flet API for required controls and services
4. Assess complexity and platform-specific risks
5. Determine appropriate scope (small/medium/large)

### Step 2: Phase Breakdown with TDD Integration
Break feature into 3-7 phases where each phase:
- **Test-First**: Write tests BEFORE implementation using pytest
- Delivers working, testable functionality
- Takes 1-4 hours maximum
- Follows Red-Green-Refactor cycle
- Has measurable test coverage requirements
- Can be rolled back independently
- Has clear success criteria
- Considers cross-platform compatibility

**Phase Structure**:
- Phase Name: Clear deliverable
- Goal: What working functionality this produces
- **Test Strategy**: pytest test types, coverage target, test scenarios
- Tasks (ordered by TDD workflow):
  1. **RED Tasks**: Write failing tests first
  2. **GREEN Tasks**: Implement minimal code to make tests pass
  3. **REFACTOR Tasks**: Improve code quality while tests stay green
- Quality Gate: TDD compliance + validation criteria
- Dependencies: What must exist before starting
- **Coverage Target**: Specific percentage or checklist for this phase
- **Platform Testing**: Which platforms to verify

### Step 3: Plan Document Creation
Use plan-template.md to generate: `docs/plans/PLAN_<feature-name>.md`

Include:
- Overview and objectives
- Architecture decisions with rationale
- Complete phase breakdown with checkboxes
- Quality gate checklists (Flet-specific)
- Risk assessment table
- Rollback strategy per phase
- Progress tracking section
- Notes & learnings area
- Platform compatibility matrix

### Step 4: User Approval
**CRITICAL**: Get explicit approval before proceeding.

Ask:
- "Does this phase breakdown make sense for your Flet project?"
- "Any concerns about the proposed approach or target platforms?"
- "Should I proceed with creating the plan document?"

Only create plan document after user confirms approval.

### Step 5: Document Generation
1. Create `docs/plans/` directory if not exists
2. Generate plan document with all checkboxes unchecked
3. Add clear instructions in header about quality gates
4. Inform user of plan location and next steps

## Flet Project Structure

### Recommended Project Layout
```
📁 my_flet_app/
├── 📄 README.md
├── 📄 pyproject.toml          # Project config & Flet build settings
├── 📄 requirements.txt        # (Optional, pyproject.toml preferred)
├── 📁 src/
│   ├── 📄 main.py             # Entry point: ft.run(main)
│   ├── 📁 assets/             # Static assets
│   │   ├── 📄 icon.png        # App icon
│   │   └── 📄 splash.png      # Splash screen (optional)
│   ├── 📁 components/         # Reusable UI components
│   │   ├── 📄 __init__.py
│   │   └── 📄 custom_controls.py
│   ├── 📁 views/              # Screen/page views
│   │   ├── 📄 __init__.py
│   │   └── 📄 home_view.py
│   ├── 📁 services/           # Business logic & data services
│   │   ├── 📄 __init__.py
│   │   └── 📄 data_service.py
│   └── 📁 utils/              # Helper utilities
│       ├── 📄 __init__.py
│       └── 📄 helpers.py
├── 📁 tests/
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py         # pytest fixtures
│   ├── 📁 unit/
│   │   └── 📄 test_services.py
│   ├── 📁 integration/
│   │   └── 📄 test_views.py
│   └── 📁 e2e/
│       └── 📄 test_app_flow.py
└── 📁 docs/
    └── 📁 plans/
        └── 📄 PLAN_feature.md
```

### pyproject.toml Configuration
```toml
[project]
name = "my-flet-app"
version = "1.0.0"
description = "Cross-platform Flet application"
readme = "README.md"
requires-python = ">=3.9"
authors = [
    { name = "Developer", email = "dev@example.com" }
]
dependencies = [
    "flet>=0.25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[tool.flet]
org = "com.mycompany"
product = "MyApp"
company = "My Company"
copyright = "Copyright (C) 2025 by My Company"
build_number = 1

[tool.flet.app]
path = "src"

# Platform-specific permissions
[tool.flet.permissions]
# Add as needed: camera, microphone, location, photo_library, etc.

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
]

[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311', 'py312']

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N", "B", "C4"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_ignores = true
```

## Quality Gate Standards

Each phase MUST validate these items before proceeding to next phase:

**Build & Run**:
- [ ] Project runs without errors: `flet run src/main.py`
- [ ] No syntax errors or import failures
- [ ] Hot reload works correctly

**Test-Driven Development (TDD)**:
- [ ] Tests written BEFORE production code
- [ ] Red-Green-Refactor cycle followed
- [ ] Unit tests: ≥80% coverage for business logic
- [ ] Integration tests: Critical user flows validated
- [ ] Test suite runs in acceptable time (<5 minutes)

**Testing**:
- [ ] All existing tests pass: `pytest tests/`
- [ ] New tests added for new functionality
- [ ] Test coverage maintained or improved: `pytest --cov=src`

**Code Quality**:
- [ ] Linting passes: `ruff check src/`
- [ ] Type checking passes: `mypy src/`
- [ ] Code formatting consistent: `black --check src/`

**Functionality**:
- [ ] Manual testing confirms feature works
- [ ] No regressions in existing functionality
- [ ] Edge cases tested

**Cross-Platform Testing**:
- [ ] Desktop: `flet run src/main.py`
- [ ] Web (if applicable): `flet run --web src/main.py`
- [ ] Mobile (if applicable): Test via Flet mobile app

**Security & Performance**:
- [ ] No new security vulnerabilities: `pip-audit`
- [ ] No performance degradation
- [ ] Resource usage acceptable

**Documentation**:
- [ ] Code comments updated
- [ ] Docstrings for public functions
- [ ] Documentation reflects changes

## Flet CLI Commands Reference

### Development Commands
```bash
# Run app in desktop mode with hot reload
flet run src/main.py

# Run in web browser
flet run --web src/main.py

# Run on specific port (web)
flet run --web --port 8080 src/main.py

# Test on mobile device
# Install Flet app on device, then:
flet run --ios   # or --android
```

### Build Commands
```bash
# Build for current platform (desktop)
flet build

# Build for specific platforms
flet build windows
flet build macos
flet build linux
flet build apk        # Android APK
flet build aab        # Android App Bundle (Play Store)
flet build ipa        # iOS (requires macOS)
flet build web        # Static web app

# Build options
flet build --build-number 2 --build-version 1.0.1
flet build --split-per-abi apk  # Split APK by architecture
```

### Project Commands
```bash
# Create new Flet project
flet create my_app

# Check Flet installation
flet doctor

# List available devices
flet devices
```

## Progress Tracking Protocol

Add this to plan document header:

```markdown
**CRITICAL INSTRUCTIONS**: After completing each phase:
1. ✅ Check off completed task checkboxes
2. 🧪 Run all quality gate validation commands
3. ⚠️ Verify ALL quality gate items pass
4. 🔄 Test on all target platforms
5. 📅 Update "Last Updated" date
6. 📝 Document learnings in Notes section
7. ➡️ Only then proceed to next phase

⛔ DO NOT skip quality gates or proceed with failing checks
```

## Phase Sizing Guidelines

**Small Scope** (2-3 phases, 3-6 hours total):
- Single component or simple feature
- Minimal platform-specific code
- Clear requirements
- Example: Add dark mode toggle, create custom control, simple form

**Medium Scope** (4-5 phases, 8-15 hours total):
- Multiple components or moderate feature
- Some platform-specific considerations
- State management complexity
- Example: Navigation system, settings page, data list with search

**Large Scope** (6-7 phases, 15-25 hours total):
- Complex feature spanning multiple areas
- Significant platform-specific code
- Multiple service integrations
- Example: Authentication system, offline-capable app, complex dashboard

## Risk Assessment

Identify and document:
- **Technical Risks**: API changes, Flutter compatibility, platform limitations
- **Platform Risks**: Different behavior on iOS/Android/Web/Desktop
- **Dependency Risks**: External library support for mobile platforms
- **Performance Risks**: Large lists, complex animations, resource usage
- **Timeline Risks**: Complexity unknowns, blocking dependencies

For each risk, specify:
- Probability: Low/Medium/High
- Impact: Low/Medium/High
- Mitigation Strategy: Specific action steps

### Flet-Specific Risk Considerations

| Risk Category | Common Issues | Mitigation |
|--------------|---------------|------------|
| Binary Packages | Some Python packages not available on mobile | Check https://pypi.flet.dev for mobile-compatible packages |
| Platform APIs | Different sensor/permission behavior | Use ft.Page.platform to detect and adapt |
| File System | Different paths on each platform | Use SharedPreferences/StoragePaths services |
| Responsive UI | Different screen sizes/orientations | Use ResponsiveRow, expand, percentage widths |
| Web Limitations | Some controls not available on web | Check API docs for web support notes |

## Rollback Strategy

For each phase, document how to revert changes if issues arise.
Consider:
- What code changes need to be undone
- Git commands for reverting: `git revert <commit>` or `git reset --hard <commit>`
- State/data changes to restore
- Dependencies to remove from pyproject.toml

## Test Specification Guidelines

### Test-First Development Workflow for Flet

**For Each Feature Component**:
1. **Specify Test Cases** (before writing ANY code)
   - What inputs/events will be tested?
   - What UI state changes are expected?
   - What edge cases must be handled?
   - What error conditions should be tested?

2. **Write Tests** (Red Phase)
   - Write tests that WILL fail
   - Verify tests fail for the right reason
   - Run tests to confirm failure
   - Commit failing tests to track TDD compliance

3. **Implement Code** (Green Phase)
   - Write minimal code to make tests pass
   - Run tests frequently
   - Stop when all tests pass
   - No additional functionality beyond tests

4. **Refactor** (Blue Phase)
   - Improve code quality while tests remain green
   - Extract duplicated logic
   - Improve naming and structure
   - Run tests after each refactoring step
   - Commit when refactoring complete

### Test Types for Flet Apps

**Unit Tests**:
- **Target**: Services, utilities, business logic, data models
- **Dependencies**: Mocked Flet controls and page
- **Speed**: Fast (<100ms per test)
- **Coverage**: ≥80% of business logic

```python
# tests/unit/test_calculator_service.py
import pytest
from src.services.calculator import CalculatorService

class TestCalculatorService:
    def test_add_positive_numbers(self):
        calc = CalculatorService()
        result = calc.add(2, 3)
        assert result == 5
    
    def test_divide_by_zero_raises_error(self):
        calc = CalculatorService()
        with pytest.raises(ValueError):
            calc.divide(10, 0)
```

**Integration Tests**:
- **Target**: Component interactions, view logic
- **Dependencies**: Mock page object
- **Speed**: Moderate (<1s per test)

```python
# tests/integration/test_counter_view.py
import pytest
from unittest.mock import MagicMock
import flet as ft
from src.views.counter_view import CounterView

class TestCounterView:
    def test_increment_updates_display(self):
        mock_page = MagicMock(spec=ft.Page)
        view = CounterView()
        view.build(mock_page)
        
        initial_value = int(view.counter_text.value)
        view.increment_click(None)
        
        assert int(view.counter_text.value) == initial_value + 1
```

**E2E Tests (Manual or Automated)**:
- **Target**: Complete user workflows
- **Speed**: Slow (seconds to minutes)
- **Approach**: Manual testing checklist or automated with UI testing tools

### Coverage Commands
```bash
# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run with verbose output
pytest -v --tb=short

# Run tests matching pattern
pytest -k "test_calculator" -v
```

### Test Coverage Thresholds
- **Business Logic/Services**: ≥90% (critical code paths)
- **Components/Views**: ≥70% (UI logic)
- **Utilities**: ≥80%
- **Overall**: ≥75%

## Flet Control Patterns

### Common UI Patterns

**Component Class Pattern**:
```python
import flet as ft

class CustomCard(ft.Container):
    def __init__(self, title: str, content: str, on_tap=None):
        super().__init__()
        self.title = title
        self.content = content
        self.on_tap = on_tap
        self._build()
    
    def _build(self):
        self.content = ft.Column([
            ft.Text(self.title, size=20, weight=ft.FontWeight.BOLD),
            ft.Text(self.content),
        ])
        self.padding = 10
        self.border_radius = 8
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        self.on_click = self.on_tap
```

**View Pattern with State**:
```python
import flet as ft

class HomeView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.counter = 0
        self._build()
    
    def _build(self):
        self.counter_text = ft.Text(str(self.counter), size=50)
        self.view = ft.View(
            "/",
            controls=[
                ft.AppBar(title=ft.Text("Counter")),
                ft.Column(
                    [
                        self.counter_text,
                        ft.Row([
                            ft.IconButton(ft.Icons.REMOVE, on_click=self._decrement),
                            ft.IconButton(ft.Icons.ADD, on_click=self._increment),
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                )
            ]
        )
    
    def _increment(self, e):
        self.counter += 1
        self.counter_text.value = str(self.counter)
        self.page.update()
    
    def _decrement(self, e):
        self.counter -= 1
        self.counter_text.value = str(self.counter)
        self.page.update()
```

### Async Pattern
```python
import flet as ft
import asyncio

async def main(page: ft.Page):
    page.title = "Async App"
    
    async def fetch_data(e):
        progress.visible = True
        page.update()
        
        await asyncio.sleep(2)  # Simulate API call
        result_text.value = "Data loaded!"
        progress.visible = False
        page.update()
    
    progress = ft.ProgressRing(visible=False)
    result_text = ft.Text("")
    
    page.add(
        ft.ElevatedButton("Load Data", on_click=fetch_data),
        progress,
        result_text,
    )

ft.run(main)
```

## Platform-Specific Considerations

### Detecting Platform
```python
import flet as ft

def main(page: ft.Page):
    if page.platform == ft.PagePlatform.IOS:
        # iOS-specific UI (Cupertino controls)
        pass
    elif page.platform == ft.PagePlatform.ANDROID:
        # Android-specific UI (Material)
        pass
    elif page.platform == ft.PagePlatform.MACOS:
        # macOS adjustments
        pass
    elif page.platform in [ft.PagePlatform.WINDOWS, ft.PagePlatform.LINUX]:
        # Desktop adjustments
        pass
    elif page.platform == ft.PagePlatform.WEB:
        # Web-specific considerations
        pass
```

### Adaptive Controls
Use adaptive controls for automatic platform styling:
```python
# Automatically uses Cupertino style on iOS, Material elsewhere
ft.Switch(adaptive=True, value=True)
ft.Slider(adaptive=True, value=50)
ft.Checkbox(adaptive=True, value=True)
```

### Permissions (Mobile)
Configure in pyproject.toml:
```toml
[tool.flet]
permissions = ["camera", "microphone", "location", "photo_library"]

[tool.flet.ios.info]
NSCameraUsageDescription = "Camera access for photos"
NSMicrophoneUsageDescription = "Microphone for recording"

[tool.flet.android.permissions]
android.permission.CAMERA = true
android.permission.RECORD_AUDIO = true
```

## Supporting Files Reference
- [plan-template.md](plan-template.md) - Complete Flet plan document template
- Flet Documentation: https://docs.flet.dev/
- Flet API Reference: https://docs.flet.dev/api-reference/
- Flet Cookbook: https://docs.flet.dev/cookbook/
- Flet GitHub: https://github.com/flet-dev/flet
