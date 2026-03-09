# Kernel Issue Automated Analysis System

**Version**: V3.0  
**Last Updated**: 2026-03-09

## 1. Project Overview

The Kernel Issue Automated Analysis System is a comprehensive platform designed to help kernel developers and maintainers efficiently manage, analyze, and resolve kernel-related issues. The system consists of four integrated components:

1. **Kernel Case Acquisition**: Automatically crawls and extracts kernel issue cases from various sources
2. **Kernel Case Structured Storage & Display**: Stores cases in a structured format and provides web interfaces for management
3. **SKILL Training**: Trains AI models using stored cases to create specialized kernel issue analysis skills
4. **Automated Kernel Issue Analysis**: Uses trained models to automatically analyze new kernel issues and provide solutions

Built with Django framework and SQLite database, the system aims to streamline the kernel issue resolution process through automation and knowledge sharing.

### 1.1 V3.0 New Features - Three-Table Architecture

The system now uses a three-table architecture to separate raw data, training data, and test data:

- **RawCase Table**: Stores raw content fetched from various sources (StackOverflow, CSDN, Zhihu, Juejin)
- **TrainingCase Table**: Stores high-quality structured cases (80%) for SKILL training
- **TestCase Table**: Stores high-quality structured cases (20%) for system testing

**Current Status**:
- RawCase: 76 records (75 pending processing)
- TrainingCase: 0 records
- TestCase: 0 records

**Key Features**:
- ✅ Multi-source fetching with intelligent delays
- ✅ HTML parsing and content extraction
- ✅ Deduplication mechanism
- ✅ Quality assessment (score ≥ 70)
- ✅ Automatic training/test set split (80%/20%)
- ✅ Vector embedding generation for RAG

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

### Part 3: SKILL Training
- **SKILL Storage**: Stores and manages specialized kernel analysis skills
- **Community SKILL Integration**: Downloads and integrates community-developed SKILLs
- **Case-based Training**: Trains SKILLs using stored kernel issue cases
- **Evaluation Metrics**: Tracks SKILL performance with accuracy and effectiveness metrics
- **SKILL Optimization**: Continuously improves SKILLs based on feedback

### Part 4: Automated Kernel Issue Analysis
- **Issue Submission**: Accepts issue descriptions and log files
- **Log Parsing**: Extracts relevant information from kernel logs
- **SKILL-based Analysis**: Uses trained SKILLs to analyze issues
- **Structured Reports**: Generates detailed analysis reports with root causes, solutions, and troubleshooting steps
- **Confidence Scoring**: Provides confidence ratings for analysis results

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
│   ├── analysis/            # SKILL training and automated analysis
│   │   ├── skill_storage.py # SKILL storage and management
│   │   ├── skill_trainer.py # SKILL training and optimization
│   │   └── issue_analyzer.py # Automated issue analysis
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
├── PROGRESS_TRACKING.md     # Project progress tracking
├── THREE_TABLES_README.md   # Three-table structure documentation
├── THREE_TABLES_SUMMARY.md  # Three-table implementation summary
└── THREE_TABLES_COMPLETION.md # Three-table completion report
```

## 5. Quick Start - Three-Table Workflow

### 5.1 Fetch Raw Cases

Fetch cases from multiple sources:

```bash
# Fetch 10 cases from StackOverflow and CSDN
python3 fetch_raw_cases.py --count 10 --sources stackoverflow csdn

# Fetch with custom keywords
python3 fetch_raw_cases.py --keywords "kernel panic" "kernel oops" --count 20

# Continuous fetching (every 30 minutes)
python3 fetch_raw_cases.py --continuous --interval 30
```

### 5.2 Process Raw Cases

Process raw cases with LLM:

```bash
# Process 10 pending cases
python3 process_raw_cases.py --batch-size 10

# Process all pending cases
python3 process_raw_cases.py --all
```

### 5.3 View Results

Check database status:

```bash
# View statistics
python3 test_three_tables.py

# View demo
python3 demo_three_tables.py
```

### 5.4 Admin Interface

Access Django admin:

```bash
# Create superuser
python3 manage.py createsuperuser

# Start server
python3 manage.py runserver

# Visit: http://localhost:8000/admin/
```

## 6. Testing

### 6.1 Test Coverage

The system has comprehensive test coverage for all components:

- **Model Tests**: Testing data model creation, validation, and relationships
- **Form Tests**: Testing form validation, field constraints, and widget configuration
- **View Tests**: Testing all view functions, URL routing, and template rendering
- **Acquisition Tests**: Testing case crawling, parsing, validation, and storage
- **SKILL Tests**: Testing SKILL storage, training, and optimization
- **Analysis Tests**: Testing automated issue analysis functionality

### 6.2 Running Tests

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

# Test SKILL components
$env:DJANGO_SETTINGS_MODULE='kernel_cases.settings'; python manage.py test cases.tests.test_skill

# Test automated analysis components
$env:DJANGO_SETTINGS_MODULE='kernel_cases.settings'; python manage.py test cases.tests.test_issue_analyzer
```

### 6.3 Test Results

All test cases have been executed and passed successfully, ensuring the system is functioning correctly.

## 7. Deployment and Running

### 7.1 Environment Requirements

- Python 3.13+
- Django 4.2+
- Required dependencies listed in requirements.txt

### 7.2 Installation Steps

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

### 7.3 Using the System Components

#### Case Acquisition
```bash
# Run case acquisition manually
python -c "from cases.acquisition.main import CaseAcquisition; ca = CaseAcquisition(); ca.run()"
```

#### SKILL Training
```bash
# Run SKILL training
python -c "from cases.analysis import SKILLStorage, SKILLTrainer; storage = SKILLStorage(); trainer = SKILLTrainer(storage); trainer.train_skill('kernel_panic_analysis')"
```

#### Automated Analysis
```python
# Use the IssueAnalyzer
from cases.analysis import SKILLStorage, IssueAnalyzer
storage = SKILLStorage()
analyzer = IssueAnalyzer(storage)

result = analyzer.analyze_issue(
    "Kernel panic due to null pointer dereference",
    "[12345.678901] BUG: kernel NULL pointer dereference, address: 0000000000000008"
)
print(result['summary'])
```

### 6.3 Production Environment Deployment

For production environment, it is recommended to:
- Use PostgreSQL or MySQL instead of SQLite
- Configure web server (e.g., Nginx) and application server (e.g., Gunicorn)
- Enable HTTPS
- Configure logging and monitoring

## 8. Documentation

- **README.md**: Project overview, testing, and deployment instructions
- **DESIGN_DOCUMENT.md**: Detailed system architecture and design documentation
- **PROGRESS_TRACKING.md**: Project progress tracking and status updates
- **THREE_TABLES_README.md**: Three-table structure documentation
- **THREE_TABLES_SUMMARY.md**: Three-table implementation summary
- **THREE_TABLES_COMPLETION.md**: Three-table completion report

## 9. Summary

The Kernel Issue Automated Analysis System is a comprehensive, production-ready platform that helps kernel developers manage, analyze, and resolve kernel issues efficiently. The system integrates case acquisition, structured storage, SKILL training, and automated analysis into a single cohesive solution.

**V3.0 Highlights**:
- Three-table architecture for better data management
- Multi-source case fetching (StackOverflow, CSDN, Zhihu, Juejin)
- Intelligent delays and deduplication
- Quality assessment and automatic training/test split
- Vector embedding for RAG functionality

With comprehensive test coverage and a modular architecture, the system provides a reliable foundation for kernel issue management and analysis. The automated analysis capabilities help reduce resolution time and improve consistency in issue handling.

For detailed architecture and design information, please refer to the DESIGN_DOCUMENT.md file. For information about project progress and status, please refer to the PROGRESS_TRACKING.md file.