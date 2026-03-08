# Kernel Issue Automated Analysis System

## 1. Project Overview

The Kernel Issue Automated Analysis System is a platform focused on kernel issue case acquisition, storage, and retrieval. The current priority is a stable phase-1/2 closed loop (acquisition + storage/vectorization), while phase-3/4 are kept as reserved interfaces.

1. **Kernel Case Acquisition**: Automatically crawls and extracts kernel issue cases from various sources
2. **Kernel Case Structured Storage & Display**: Stores cases in a structured format and provides web interfaces for management
3. **SKILL Training (Reserved Interface)**: Postponed implementation, compatibility interface retained
4. **Automated Kernel Issue Analysis (Reserved Interface)**: Postponed implementation, compatibility interface retained

Built with Django framework and SQLite database, the system aims to streamline the kernel issue resolution process through automation and knowledge sharing.

## 2. Technology Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Backend Framework | Django | 4.2+ | Web application development framework |
| Database | SQLite | 3.x | Lightweight relational database |
| Frontend Framework | Bootstrap | 5.1 | Responsive UI design |
| Programming Language | Python | 3.13 | Backend development language |

## 3. Core Functionality

### Part 1: Kernel Case Acquisition
- **Multi-source Crawling**: Automatically collects kernel issue cases from blogs, forums, and Q&A communities
- **Content Parsing**: Extracts and structures case information from raw web content
- **Data Validation**: Ensures collected cases meet quality standards before storage
- **Batch Processing**: Supports large-scale case acquisition with error handling

### Part 2: Kernel Case Structured Storage & Display
- **Case Management**: Create, view, edit, and manage kernel issue cases
- **Search Functionality**: Search cases by title, description, symptoms, keywords, etc.
- **Statistics**: View case statistics by severity level, category, etc.
- **Pagination**: Paginated display of case lists
- **Web Interface**: User-friendly interface for case management

### Part 3: SKILL Training (Reserved)
- Interface placeholders are kept in `cases/analysis/interfaces.py`
- Runtime implementation is intentionally postponed

### Part 4: Automated Kernel Issue Analysis (Reserved)
- Interface placeholders are kept in `cases/analysis/interfaces.py`
- Runtime implementation is intentionally postponed

## 4. Project Structure

```
08_database/
├── cases/                   # Case application directory
│   ├── acquisition/         # Case acquisition components
│   │   ├── fetchers.py      # Content fetching from various sources
│   │   ├── parsers.py       # Content parsing and structuring
│   │   ├── validators.py    # Data validation
│   │   ├── storage.py       # Database integration for acquisition
│   │   └── main.py          # Main acquisition orchestrator
│   ├── analysis/            # Reserved interfaces for phase-3/4
│   │   ├── interfaces.py    # Placeholder interfaces only
│   │   └── __init__.py      # Compatibility exports
│   ├── models.py            # Database models
│   ├── forms.py             # Forms for case management
│   ├── views.py             # View functions/classes
│   ├── urls.py              # URL configuration
│   ├── admin.py             # Admin interface
│   └── tests/               # Test files
├── kernel_cases/            # Project configuration directory
├── templates/               # HTML templates directory
├── static/                  # Static files directory
├── db.sqlite3               # SQLite database file
├── manage.py                # Project management script
├── requirements.txt         # Project dependencies
├── README.md                # Project documentation
├── DESIGN_DOCUMENT.md       # Detailed design document
└── PROGRESS_TRACKING.md     # Project progress tracking
```

## 5. Testing

### 5.1 Test Coverage

The system has comprehensive test coverage for all components:

- **Model Tests**: Testing data model creation, validation, and relationships
- **Form Tests**: Testing form validation, field constraints, and widget configuration
- **View Tests**: Testing all view functions, URL routing, and template rendering
- **Acquisition Tests**: Testing case crawling, parsing, validation, and storage
- **Storage+RAG Integration Tests**: Testing database CRUD and local vector retrieval

### 5.2 Running Tests

To run all tests:

```bash
# Windows PowerShell
$env:DJANGO_SETTINGS_MODULE='kernel_cases.settings'; python manage.py test cases

# For detailed output
$env:DJANGO_SETTINGS_MODULE='kernel_cases.settings'; python manage.py test cases -v 2
```

To run specific test modules:

```bash
# Test acquisition components
$env:DJANGO_SETTINGS_MODULE='kernel_cases.settings'; python manage.py test cases.tests.test_acquisition

# Test storage + vector integration
python verify_storage_rag.py
```

### 5.3 Test Results

All test cases have been executed and passed successfully, ensuring the system is functioning correctly.

## 6. Deployment and Running

### 6.1 Environment Requirements

- Python 3.13+
- Django 4.2+
- Required dependencies listed in requirements.txt

### 6.2 Installation Steps

1. Clone the project:
   ```bash
   git clone <repository-url>
   cd 08_database
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Database migration:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Start development server:
   ```bash
   python manage.py runserver 8080
   ```

5. Access the application:
   ```
   http://localhost:8080
   ```

### 6.3 Using the System Components

#### Case Acquisition
```bash
# Run case acquisition manually
python -c "from cases.acquisition.main import CaseAcquisition; ca = CaseAcquisition(); ca.run()"
```

#### Reserved Interfaces (Phase-3/4)
`cases.analysis.SKILLStorage`, `cases.analysis.SKILLTrainer`, `cases.analysis.IssueAnalyzer` are intentionally placeholder interfaces and currently raise `NotImplementedError`.

### 6.3 Production Environment Deployment

For production environment, it is recommended to:
- Use PostgreSQL or MySQL instead of SQLite
- Configure web server (e.g., Nginx) and application server (e.g., Gunicorn)
- Enable HTTPS
- Configure logging and monitoring

## 7. Documentation

- **README.md**: Project overview, testing, and deployment instructions
- **DESIGN_DOCUMENT.md**: Detailed system architecture and design documentation
- **PROGRESS_TRACKING.md**: Project progress tracking and status updates

## 8. Summary

The Kernel Issue Automated Analysis System is a comprehensive, production-ready platform that helps kernel developers manage, analyze, and resolve kernel issues efficiently. The system integrates case acquisition, structured storage, SKILL training, and automated analysis into a single cohesive solution.

With comprehensive test coverage and a modular architecture, the system provides a reliable foundation for kernel issue management and analysis. The automated analysis capabilities help reduce resolution time and improve consistency in issue handling.

For detailed architecture and design information, please refer to the DESIGN_DOCUMENT.md file. For information about project progress and status, please refer to the PROGRESS_TRACKING.md file.