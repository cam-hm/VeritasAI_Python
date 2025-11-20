# Coding Standards - Python/Django

## 🎯 Python Coding Standards

### PEP 8 - Style Guide for Python Code

**Tương đương với PSR-12 trong PHP/Laravel**

#### Key Rules:

1. **Indentation**: 4 spaces (không dùng tabs)
2. **Line length**: Maximum 79-99 characters
3. **Imports**: 
   - Standard library imports
   - Related third party imports
   - Local application/library specific imports
   - Mỗi group cách nhau 1 dòng trống
4. **Naming conventions**:
   - `snake_case` cho functions, variables
   - `PascalCase` cho classes
   - `UPPER_CASE` cho constants
   - `_single_leading_underscore` cho internal use
   - `__double_leading_underscore` cho name mangling
5. **Whitespace**: 
   - 2 blank lines giữa top-level definitions
   - 1 blank line giữa methods trong class
6. **Comments**: 
   - Docstrings cho modules, classes, functions
   - Inline comments khi cần giải thích

#### Tools:

- **Black**: Code formatter (tương đương Laravel Pint)
- **flake8**: Linter (tương đương PHP_CodeSniffer)
- **isort**: Import sorter
- **mypy**: Type checker (tương đương PHPStan)

---

## 🏗️ Django Best Practices

### Project Structure

```
project/
├── manage.py
├── project_name/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── app_name/
│   ├── models.py          # Hoặc models/ folder
│   ├── views.py            # Hoặc views/ folder
│   ├── serializers.py      # Hoặc serializers/ folder
│   ├── urls.py
│   ├── admin.py
│   └── services/
│       └── ...
```

### Models Organization

#### Option 1: Single `models.py` (Current - OK for small projects)
```
app/
└── models.py  # Tất cả models trong 1 file
```

**Khi nào dùng:**
- ✅ < 5-7 models
- ✅ Models đơn giản
- ✅ MVP/small projects

**Pros:**
- Đơn giản
- Dễ tìm
- Django default

**Cons:**
- File lớn khi có nhiều models
- Khó maintain khi phức tạp

#### Option 2: `models/` Package (Recommended for larger projects)
```
app/
└── models/
    ├── __init__.py         # Export all models
    ├── document.py         # Document, DocumentChunk
    ├── chat.py             # ChatSession, ChatMessage
    └── base.py             # Base models, mixins
```

**Khi nào dùng:**
- ✅ > 5-7 models
- ✅ Models phức tạp
- ✅ Multiple domains
- ✅ Production projects

**Pros:**
- Tổ chức tốt hơn
- Dễ maintain
- Scalable
- Clear separation

**Cons:**
- Phức tạp hơn
- Cần quản lý imports

---

## 📋 Current Project Analysis

### Current State:
- **4 models**: Document, DocumentChunk, ChatSession, ChatMessage
- **1 file**: `models.py` (259 lines)
- **Status**: ✅ OK cho MVP

### Recommendation:
- **Hiện tại**: Giữ nguyên 1 file `models.py` (đủ tốt cho MVP)
- **Khi nào refactor**: 
  - Khi có > 7 models
  - Khi models phức tạp hơn
  - Khi cần thêm domains (analytics, billing, etc.)

---

## 🔧 Tools Setup

### 1. Black (Code Formatter)

```bash
pip install black
```

**Usage:**
```bash
black app/
```

**Config** (`pyproject.toml`):
```toml
[tool.black]
line-length = 88
target-version = ['py313']
include = '\.pyi?$'
```

### 2. flake8 (Linter)

```bash
pip install flake8
```

**Usage:**
```bash
flake8 app/
```

**Config** (`.flake8`):
```ini
[flake8]
max-line-length = 88
exclude = 
    migrations,
    venv,
    __pycache__
```

### 3. isort (Import Sorter)

```bash
pip install isort
```

**Usage:**
```bash
isort app/
```

**Config** (`pyproject.toml`):
```toml
[tool.isort]
profile = "black"
line_length = 88
```

### 4. mypy (Type Checker)

```bash
pip install mypy
```

**Usage:**
```bash
mypy app/
```

---

## 📝 Code Examples

### Good (PEP 8 compliant):

```python
from django.db import models
from django.core.exceptions import ValidationError


class Document(models.Model):
    """Document model - User's uploaded documents."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    def get_formatted_file_size(self):
        """Get formatted file size (e.g., '2.5 MB')."""
        if not self.file_size:
            return "Unknown"
        # ... implementation
```

### Bad (Not PEP 8 compliant):

```python
from django.db import models
from django.core.exceptions import ValidationError
class Document(models.Model):
    STATUS_CHOICES=[('pending','Pending'),('processing','Processing')]
    name=models.CharField(max_length=255)
    def get_formatted_file_size(self):
        if not self.file_size:return "Unknown"
```

---

## 🎯 Django-Specific Conventions

### 1. Model Naming
- ✅ `PascalCase`: `Document`, `ChatSession`
- ✅ Singular: `Document` (not `Documents`)
- ✅ Descriptive: `ChatMessage` (not `Message`)

### 2. Field Naming
- ✅ `snake_case`: `created_at`, `file_hash`
- ✅ Descriptive: `last_message_at` (not `last_msg`)

### 3. Method Naming
- ✅ `snake_case`: `get_formatted_file_size()`
- ✅ Verb-based: `get_`, `create_`, `update_`, `delete_`

### 4. Constants
- ✅ `UPPER_CASE`: `STATUS_CHOICES`, `ROLE_CHOICES`

### 5. Related Names
- ✅ Plural: `related_name='documents'` (not `document`)
- ✅ Descriptive: `related_name='chat_messages'`

---

## 📚 References

- **PEP 8**: https://pep8.org/
- **Django Style Guide**: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/
- **Two Scoops of Django**: https://www.feldroy.com/books/two-scoops-of-django-3-x
- **Black**: https://black.readthedocs.io/
- **flake8**: https://flake8.pycqa.org/

---

## ✅ Checklist

- [ ] Code follows PEP 8
- [ ] Use Black for formatting
- [ ] Use flake8 for linting
- [ ] Use isort for import sorting
- [ ] Models organized appropriately
- [ ] Docstrings for all classes/functions
- [ ] Type hints where appropriate
- [ ] Consistent naming conventions

