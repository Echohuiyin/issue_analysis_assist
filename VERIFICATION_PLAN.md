# Kernel Issue Automated Analysis System - Verification Plan

This document outlines the step-by-step verification plan for the Kernel Issue Automated Analysis System. The verification is designed incrementally, starting from the first component and gradually integrating subsequent components to ensure the entire pipeline works seamlessly.

## Phase 1: Verify Part 1 (Kernel Case Acquisition)

**Objective:** Ensure the system can successfully fetch, parse, validate, and store real kernel cases from external sources (e.g., StackOverflow API), replacing any hardcoded mock data.

**Verification Steps:**
1. **Code Refactoring (Remove Hardcoding):**
   - Update `cases/acquisition/fetchers.py` and `cases/acquisition/parsers.py` to support real API endpoints (like StackExchange API for StackOverflow).
   - Remove hardcoded mock data from parsers and implement actual JSON/HTML parsing logic to extract `title`, `phenomenon`, `root_cause`, etc.
2. **Unit Tests:** Run the acquisition unit tests to verify the core logic of fetchers, parsers, validators, and storage components in isolation. Fix any tests broken by the removal of hardcoded data.
   - Command: `python manage.py test cases.tests.test_acquisition`
3. **Real Data Acquisition Test:** Create and run a standalone script (e.g., `verify_acquisition.py`) that initializes the `CaseAcquisition` pipeline and fetches a small number of real cases (e.g., 2-3 cases) from a live API (like StackOverflow).
4. **Database Inspection:** After running the script, inspect the SQLite database (`db.sqlite3`) to confirm that new records have been inserted into the `cases_case` table. Verify that the structured fields are correctly populated with the real data fetched from the API.

## Phase 2: Verify Part 1 + Part 2 (Acquisition + Storage & Display)

**Objective:** Ensure that acquired cases are correctly stored in the database and can be properly managed, searched, and displayed through the Django web interface.

**Verification Steps:**
1. **Prerequisite:** Complete Phase 1 to ensure there is actual case data in the database.
2. **Unit Tests:** Run the models, views, and forms unit tests to ensure the web layer logic is sound.
   - Command: `python manage.py test cases.tests.test_models cases.tests.test_views cases.tests.test_forms`
3. **Web Interface - List & Search:** Start the Django development server (`python manage.py runserver`). Navigate to the case list page (e.g., `http://localhost:8000/cases/` or the configured root URL). Verify that the cases acquired in Phase 1 are displayed correctly in the list. Test the search functionality by searching for specific keywords present in the acquired cases to ensure the search filters work.
4. **Web Interface - Detail View:** Click on a specific case from the list to view its details. Verify that all structured fields (phenomenon, root cause, solution, environment, etc.) are rendered correctly on the page.
5. **Admin Interface:** Log in to the Django admin panel (`http://localhost:8000/admin/`). Verify that cases can be viewed, edited, and deleted through the admin interface, confirming full CRUD capabilities.

## Phase 3: Verify Part 1 + Part 2 + Part 3 (Acquisition + Storage & Display + SKILL Training)

**Objective:** Ensure that the system can use the stored cases (acquired in Part 1 and managed in Part 2) to train and optimize SKILLs (AI models/rules).

**Verification Steps:**
1. **Prerequisite:** Complete Phase 1 and Phase 2. Ensure there are sufficient cases in the database to serve as training data.
2. **Unit Tests:** Run the SKILL training unit tests.
   - Command: `python manage.py test cases.tests.test_skill`
3. **Community SKILL Integration:** Run a script or command to test downloading and integrating community SKILLs. Verify that the SKILL files are saved in the `community_skills/` directory and properly registered in the system's storage.
4. **SKILL Training Execution:** Run a script to trigger the SKILL training process (e.g., calling `SKILLTrainer.train_all_skills()`). This process should read cases from the database.
5. **Training Results Inspection:** Verify that the trained/optimized SKILLs are saved in the `skills/` directory. Check the logs or output for evaluation metrics (e.g., accuracy, confidence improvements) to ensure the training loop is functioning and actually utilizing the database cases to optimize the SKILLs.

## Phase 4: Verify Part 1 + Part 2 + Part 3 + Part 4 (Full System Integration including Automated Analysis)

**Objective:** Ensure the complete end-to-end workflow: cases are acquired, stored, used for training SKILLs, and finally, these trained SKILLs are used to automatically analyze new, unseen kernel issues.

**Verification Steps:**
1. **Prerequisite:** Complete Phases 1, 2, and 3. Ensure trained SKILLs are available in the `skills/` directory.
2. **Unit Tests:** Run the automated analysis unit tests.
   - Command: `python manage.py test cases.tests.test_issue_analyzer`
3. **Automated Analysis Execution:** Create a script (e.g., `verify_analyzer.py`) that instantiates the `IssueAnalyzer`.
4. **Mock Issue Submission:** Feed a mock kernel issue description and a sample kernel log (e.g., a typical kernel panic log or OOM log) to the `analyze_issue` method of the analyzer.
5. **Result Verification:** Inspect the output of the analysis. Verify that it successfully utilizes the trained SKILLs and returns a structured report containing:
   - A summary of the issue.
   - The identified root cause.
   - Recommended troubleshooting steps.
   - Potential solutions.
   - A confidence score indicating the reliability of the analysis.
6. **End-to-End Web Test (If applicable):** If the web interface includes a feature for users to submit issues for analysis, use it to upload a log file and description. Verify that the backend processes it correctly and the analysis report is displayed properly on the web page.