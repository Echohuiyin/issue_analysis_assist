# Kernel Issue Case Management System

## 1. Project Overview

The Kernel Issue Case Management System is a web application designed to record, manage, and query kernel-related issue cases. Built with Django framework and SQLite database, it provides functions for case CRUD operations, search, and statistics, aiming to help kernel developers and maintainers efficiently manage and share kernel issue solving experiences.

## 2. Technology Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Backend Framework | Django | 4.2+ | Web application development framework |
| Database | SQLite | 3.x | Lightweight relational database |
| Frontend Framework | Bootstrap | 5.1 | Responsive UI design |
| Programming Language | Python | 3.13 | Backend development language |

## 3. Core Functionality

- **Case Management**: Create, view, and manage kernel issue cases
- **Search Functionality**: Search cases by multiple fields including title, description, symptoms, etc.
- **Statistics**: View case statistics by severity level
- **Pagination**: Paginated display of case lists (20 cases per page)

## 4. Project Structure

```
08_database/
├── cases/                   # Case application directory
├── kernel_cases/            # Project configuration directory
├── templates/               # HTML templates directory
├── static/                  # Static files directory
├── db.sqlite3               # SQLite database file
├── manage.py                # Project management script
├── requirements.txt         # Project dependencies
├── README.md                # Project documentation
└── DESIGN_DOCUMENT.md       # Detailed design document
```

## 5. Testing

### 5.1 Test Coverage

The system has comprehensive test coverage including:

- **Model Tests**: Testing data model creation, validation, and relationships
- **Form Tests**: Testing form validation, field constraints, and widget configuration
- **View Tests**: Testing all view functions, URL routing, and template rendering

### 5.2 Running Tests

To run tests, use the following command:

```bash
# Windows PowerShell
$env:DJANGO_SETTINGS_MODULE='kernel_cases.settings'; python manage.py test cases

# For detailed output
$env:DJANGO_SETTINGS_MODULE='kernel_cases.settings'; python manage.py test cases -v 2
```

### 5.3 Test Results

All 21 test cases have been executed and passed successfully, ensuring the system is functioning correctly.

## 6. Deployment and Running

### 6.1 Environment Requirements

- Python 3.13+
- Django 4.2+

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

### 6.3 Production Environment Deployment

For production environment, it is recommended to:
- Use PostgreSQL or MySQL instead of SQLite
- Configure web server (e.g., Nginx) and application server (e.g., Gunicorn)
- Enable HTTPS
- Configure logging and monitoring

## 7. Documentation

- **README.md**: Project overview, testing, and deployment instructions
- **DESIGN_DOCUMENT.md**: Detailed system architecture and design documentation

## 8. Summary

The Kernel Issue Case Management System is a complete, production-ready web application that helps kernel developers manage and share issue cases efficiently. The system has passed all 21 test cases, ensuring its reliability and correctness. For detailed architecture and design information, please refer to the DESIGN_DOCUMENT.md file.