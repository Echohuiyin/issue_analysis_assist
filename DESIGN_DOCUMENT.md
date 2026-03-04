# Kernel Issue Case Management System - Design Document

## 1. Project Overview

The Kernel Issue Case Management System is a web application designed to record, manage, and query kernel-related issue cases. Built with Django framework and SQLite database, it provides functions for case CRUD operations, search, and statistics, aiming to help kernel developers and maintainers efficiently manage and share kernel issue solving experiences.

## 2. Technology Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Backend Framework | Django | 4.2+ | Web application development framework |
| Database | SQLite | 3.x | Lightweight relational database |
| Frontend Framework | Bootstrap | 5.1 | Responsive UI design |
| Programming Language | Python | 3.13 | Backend development language |

## 3. Architecture Pattern

The system adopts the classic MVC (Model-View-Controller) architecture pattern, separating business logic, data representation, and user interface.

### 3.1 MVC Architecture Diagram

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|      View        |     |   Controller     |     |      Model       |
|                  |     |                  |     |                  |
|  (HTML templates)| <--> |  (Class-based    | <--> |  (Database       |
|                  |     |   views in       |     |   models)        |
|                  |     |   Django)        |     |                  |
+------------------+     +------------------+     +------------------+
         ^                           |
         |                           v
+------------------+     +------------------+
|                  |     |                  |
|    User Browser  |     |     Database     |
|                  |     |                  |
+------------------+     +------------------+
```

## 4. Core Components Design

### 4.1 Data Model Layer (Model)

The data model layer defines the system's data structure and database interactions.

#### 4.1.1 KernelCase Model

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | Integer | Primary Key | Auto-incrementing primary key |
| case_id | String(50) | Unique, Not Null | Case ID |
| title | String(200) | Not Null | Case title |
| description | Text | Not Null | Case description |
| symptoms | Text | Not Null | Problem symptoms |
| root_cause | Text | Not Null | Root cause |
| solution | Text | Not Null | Solution |
| kernel_version | String(50) | Not Null | Kernel version |
| affected_components | String(200) | Not Null | Affected components |
| severity | String(20) | Not Null | Severity level (Low, Medium, High, Critical) |
| created_date | DateTime | Default: now | Creation time |
| updated_date | DateTime | Auto: update | Update time |

#### 4.1.2 Model Methods

1. **severity_display** (property): Returns the display text for severity level
2. **search** (classmethod): Performs multi-field search based on keywords
3. **get_severity_stats** (classmethod): Gets statistics grouped by severity level

### 4.2 Business Logic Layer (Controller)

The business logic layer is implemented using Django's class-based views, which handle user requests and return responses.

#### 4.2.1 Core View Classes

| View Class | URL Path | Description |
|------------|----------|-------------|
| `CaseListView` | `/` | Display case list with pagination |
| `CaseDetailView` | `/case/<int:pk>/` | Display single case details |
| `CaseCreateView` | `/add/` | Handle case addition form |
| `SearchView` | `/search/` | Perform case search functionality |
| `StatsView` | `/stats/` | Display case statistics |

#### 4.2.2 Business Flow

1. **Case Query Flow**:
   - User visits home page -> View gets case list -> Pagination -> Render template -> Return response

2. **Case Addition Flow**:
   - User visits add page -> Render form -> User submits -> Form validation -> Save to database -> Redirect to home page

3. **Case Search Flow**:
   - User enters keywords -> Submit search request -> View performs multi-field query -> Pagination -> Render results

4. **Statistics Flow**:
   - User visits stats page -> View gets statistics -> Render template -> Return response

### 4.3 Presentation Layer (View)

The presentation layer is implemented with HTML templates, using Bootstrap framework to build responsive user interfaces.

#### 4.3.1 Template Structure

- **base.html**: Base template defining page layout and navigation
- **index.html**: Case list page showing paginated case lists
- **case_detail.html**: Case detail page displaying complete case information
- **add_case.html**: Case addition page containing form inputs
- **stats.html**: Statistics page showing case statistics charts

#### 4.3.2 Custom Template Tags

1. **severity_class**: Returns the corresponding CSS class based on severity level
2. **severity_display**: Returns the corresponding display text based on severity level

## 5. Database Design

### 5.1 Database Table Structure

The system uses SQLite database with one core table:

**cases_kernelcase table**

| Field Name | Data Type | Constraints |
|------------|-----------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| case_id | VARCHAR(50) | NOT NULL UNIQUE |
| title | VARCHAR(200) | NOT NULL |
| description | TEXT | NOT NULL |
| symptoms | TEXT | NOT NULL |
| root_cause | TEXT | NOT NULL |
| solution | TEXT | NOT NULL |
| kernel_version | VARCHAR(50) | NOT NULL |
| affected_components | VARCHAR(200) | NOT NULL |
| severity | VARCHAR(20) | NOT NULL |
| created_date | DATETIME | NOT NULL |
| updated_date | DATETIME | NULL |

### 5.2 Index Design

- id field: Primary key index for quick lookup and sorting
- case_id field: Unique index to ensure case ID uniqueness
- created_date field: Used for sorting by creation time

## 6. URL Design

| URL Path | View Class | Purpose |
|----------|------------|---------|
| `/` | CaseListView | Case list page |
| `/case/<int:pk>/` | CaseDetailView | Case detail page |
| `/add/` | CaseCreateView | Add case page |
| `/search/` | SearchView | Search page |
| `/stats/` | StatsView | Statistics page |

## 7. Forms Design

### 7.1 KernelCaseForm

- **Model**: KernelCase
- **Excluded Fields**: created_date, updated_date
- **Widget Customization**:
  - description: Textarea (3 rows)
  - symptoms: Textarea (4 rows)
  - root_cause: Textarea (4 rows)
  - solution: Textarea (4 rows)

## 8. Extensibility Design

The system adopts modular design for easy future expansion:

1. **Function Expansion**:
   - Easily add case editing and deletion functionality
   - Support exporting cases to PDF or Excel formats
   - Add user authentication and permission management

2. **Data Expansion**:
   - Add more fields such as attachments, screenshots, etc.
   - Support case categorization and tagging functions

3. **Performance Expansion**:
   - Optimize database queries and add more indexes
   - Support caching mechanism to improve query performance
   - Expand to distributed architecture

## 9. Security Considerations

1. **Input Validation**: All user inputs are validated through Django forms
2. **SQL Injection Prevention**: Use Django ORM to avoid SQL injection attacks
3. **XSS Protection**: Django automatically escapes template variables
4. **CSRF Protection**: Django includes CSRF tokens in all forms
5. **Data Integrity**: Use unique constraints and required fields to ensure data integrity

## 10. Performance Considerations

1. **Pagination**: Limit the number of cases displayed per page (default 20)
2. **Query Optimization**: Use appropriate indexes and avoid unnecessary database queries
3. **Caching**: Consider implementing caching for frequently accessed data
4. **Database Design**: Normalize the database structure to avoid data redundancy

## 11. Project Structure

```
08_database/
├── cases/                   # Case application directory
│   ├── __init__.py          # Application initialization file
│   ├── admin.py             # Backend management configuration
│   ├── apps.py              # Application configuration
│   ├── forms.py             # Form definitions
│   ├── models.py            # Data models
│   ├── templatetags/        # Custom template tags
│   │   ├── __init__.py      # Template tags package initialization
│   │   └── case_tags.py     # Case-related template tags
│   ├── tests/               # Test files directory
│   │   ├── __init__.py      # Test package initialization
│   │   ├── test_forms.py    # Form tests
│   │   ├── test_models.py   # Model tests
│   │   └── test_views.py    # View tests
│   ├── urls.py              # Application URL configuration
│   └── views.py             # View functions/classes
├── kernel_cases/            # Project configuration directory
│   ├── __init__.py          # Project initialization
│   ├── settings.py          # Project settings
│   ├── urls.py              # Project URL configuration
│   └── wsgi.py              # WSGI configuration
├── templates/               # HTML templates directory
│   ├── base.html            # Base template
│   └── cases/               # Case application templates
│       ├── add_case.html    # Add case template
│       ├── case_detail.html # Case detail template
│       ├── index.html       # Case list template
│       └── stats.html       # Statistics template
├── static/                  # Static files directory
├── db.sqlite3               # SQLite database file
├── manage.py                # Project management script
├── requirements.txt         # Project dependencies
├── README.md                # Project documentation
└── DESIGN_DOCUMENT.md       # Design document
```

## 12. Project Progress Tracking

### Phase 1: Kernel Case Acquisition
- [x] Design document completed
- [x] Test cases written for all components
- [x] Implementation of core components (fetchers, parsers, validators, storage, main)
- [x] Integration testing completed

### Phase 2: Structured Storage and Display
- [x] Design document completed
- [x] Test cases written for all components
- [x] Implementation completed
- [x] Integration testing completed

### Phase 3: SKILL Training
- [x] Design document completed
- [x] Test cases written for all components
- [x] Implementation of SKILL storage module
- [x] Implementation of SKILL training module
- [x] Integration testing completed

### Phase 4: Automated Analysis
- [x] Design document completed
- [x] Test cases written for all components
- [x] Implementation of IssueAnalyzer module
- [x] Integration testing completed