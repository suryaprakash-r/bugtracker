# BugTracker — Django Bug Tracking System

A professional, role-based **Bug Tracking System** built with Django. The project is designed to manage software projects, track bugs through a controlled lifecycle, support team collaboration, provide reporting and exports, and give administrators secure user management.

> **Current release:** v1.0.0 — Stable
>
> **v1.0 status:** Development, functional validation, responsive validation, and final regression testing completed.

---

## Overview

BugTracker provides a centralized workspace for software teams to:

- Manage projects and project members
- Create, assign, update, and track bugs
- Control bug status transitions
- Add comments and attachments
- Maintain bug status history
- Receive and manage notifications
- Generate filtered reports and export them as CSV/PDF
- Manage users through role-based access control
- Manage personal profiles, passwords, and password-reset workflows

The application uses a reusable base layout and centralized message notification component so common UI behavior remains consistent across modules.

---

## Core Features

### Dashboard

- Project and bug KPI cards
- Bug status analytics
- Bug trend visualization
- Recent bugs
- Recent activity
- Role-aware dashboard visibility

### Project Management

- Project creation and editing
- Project status management
- Project manager assignment
- Project member management
- Member activation/deactivation
- Role-aware project visibility

### Bug Management

- Bug creation and editing
- Unique bug codes
- Severity and priority classification
- Environment tracking
- Reporter and assignee handling
- Controlled status workflow
- Comments
- File attachments
- Bug status history
- Role-aware bug visibility and actions

### Notifications

- Bug assignment notifications
- Status-change notifications
- Comment notifications
- Project membership notifications
- Read/unread notification management
- Centralized application message notifications

### Reports

- Bug summary and analytics
- Status, severity, and priority breakdowns
- Project-based reporting
- Date filtering
- Pagination
- CSV export
- PDF export
- Role-based report access

### User Management

Available to authorized administrators:

- User directory
- Search and filtering
- Add user
- Edit user
- Activate/deactivate user
- Delete user
- Self-delete protection
- Protected relationship handling during deletion
- Automatic profile creation for new users

### Account & Profile Management

- Login and logout
- Profile view
- Profile editing
- Profile image upload
- Password change
- Forgot-password workflow
- Password-reset confirmation
- Custom 403 Access Denied page

---

## Role-Based Access Control

BugTracker uses four application roles:

| Role | Purpose |
| --- | --- |
| **Admin** | Full system administration, user management, project/bug/report access |
| **Project Manager** | Manage assigned projects, members, bugs, and reports within accessible scope |
| **Developer** | Work with bugs and projects available through active membership |
| **Tester** | Test and update bugs within accessible projects and workflows |

Authorization is centralized through the accounts permission layer rather than being duplicated across individual views.

---

## Technology Stack

### Backend

- Python 3.14.3
- Django 6.1.1
- Django authentication system
- Django messages framework

### Database

- SQLite for the current v1.0 development/application baseline

### Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap
- Bootstrap Icons

### Reporting & Documents

- ReportLab for PDF generation
- CSV export through Django/Python response handling

### File Handling

- Pillow for image processing
- Django media/static file handling

---

## Application Structure

```text
bugtracker/
│
├── apps/
│   ├── accounts/
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── permissions.py
│   │   ├── urls.py
│   │   └── views.py
│   │
│   ├── dashboard/
│   ├── projects/
│   ├── bugs/
│   ├── notifications/
│   └── reports/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── templates/
│   ├── base/
│   ├── accounts/
│   ├── users/
│   ├── projects/
│   ├── bugs/
│   ├── notifications/
│   ├── reports/
│   └── 403.html
│
├── static/
│   ├── css/
│   └── js/
│
├── media/
├── manage.py
└── README.md
```

---

## Main Data Model

The v1.0 application is centered around the following entities:

```text
User
 ├── Profile
 ├── Managed Projects
 ├── Project Memberships
 ├── Reported Bugs
 ├── Assigned Bugs
 ├── Bug Comments
 ├── Bug Attachments
 ├── Bug Status Changes
 ├── Notifications
 └── Activity Logs

Project
 ├── Manager
 ├── Project Members
 ├── Bugs
 ├── Notifications
 └── Activity Logs

Bug
 ├── Project
 ├── Reporter
 ├── Assignee
 ├── Comments
 ├── Attachments
 ├── Status History
 └── Notifications
```

The model relationships also use protected deletion rules where historical ownership or audit integrity must be preserved. For example, reporter, attachment uploader, status-history actor, and project-manager relationships are protected from unsafe user deletion.

---

## Bug Lifecycle

BugTracker supports the following bug states:

```text
NEW
  ↓
ASSIGNED
  ↓
IN_PROGRESS
  ↓
RESOLVED
  ↓
TESTING
  ↓
CLOSED
```

The application also supports:

```text
REOPENED
```

Status changes are controlled by the application's bug workflow rules and are recorded in `BugStatusHistory`.

---

## Installation & Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/suryaprakash-r/bugtracker
cd bugtracker
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
Linux:

```powershell
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Run migrations

```powershell
python manage.py migrate
```

### 5. Create an administrator

```powershell
python manage.py createsuperuser
```

### 6. Run system checks

```powershell
python manage.py check
```

### 7. Start the development server

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

## Configuration Notes

The project uses Django settings for authentication, static/media files, database access, and email functionality.

For development, the password-reset workflow can use Django's console email backend so reset emails are displayed in the terminal rather than sent through an external mail service.

For production deployment, configure a real SMTP/email provider and production-ready database, static file storage, media storage, secrets, HTTPS, and deployment settings.

---

## Security & Data Integrity

The application includes several protections in the v1.0 baseline:

- Authentication required for protected application pages
- Centralized RBAC permission checks
- CSRF protection for POST forms
- Inactive users cannot authenticate
- Admin-only user-management controls
- Self-delete protection
- POST-only destructive user actions
- Protected user relationships using Django `PROTECT`
- Controlled bug-status transitions
- Custom 403 page for forbidden access
- Role-aware project and bug querysets

---

## Reporting & Export

The Reports module supports:

- Summary statistics
- Status distribution
- Severity and priority breakdowns
- Project reporting
- Date-based filtering
- Pagination
- Full CSV export
- Filtered CSV export
- Full PDF export
- Filtered PDF export

The v1.0 reporting implementation follows the existing application RBAC rules. Developer/Tester report visibility remains reserved for the planned v2.0 reporting redesign.

---

## UI / UX Design

The application follows a consistent professional dashboard style:

- Dark navy sidebar
- Light content surfaces and cards
- Blue primary accents
- Soft/pastel status indicators
- Responsive tables and forms
- Consistent action buttons
- Centralized application messages
- Responsive navigation for laptop, tablet, and mobile layouts

The global Django message component uses the same notification visual language established in the completed Profile section and is reused throughout the application.

---

## Validation Status — v1.0

The v1.0 release was validated across the main functional areas:

| Area | Status |
| --- | --- |
| Authentication | ✅ Passed |
| RBAC | ✅ Passed |
| Dashboard | ✅ Passed |
| Projects | ✅ Passed |
| Project Members | ✅ Passed |
| Bugs | ✅ Passed |
| Comments & Attachments | ✅ Passed |
| Bug Status Workflow | ✅ Passed |
| Notifications | ✅ Passed |
| Reports | ✅ Passed |
| CSV/PDF Export | ✅ Passed |
| User Management | ✅ Passed |
| Profile Management | ✅ Passed |
| Password Change / Reset | ✅ Passed |
| 403 Access Control | ✅ Passed |
| Responsive Validation | ✅ Passed |
| Final Regression | ✅ Passed |

---

## Version Roadmap

### v1.0 — Completed

Core BugTracker functionality, authentication, RBAC, project and bug management, notifications, reports, user management, profile management, responsive UI, and regression validation.

### v2.0 — Planned

Potential future improvements include a redesigned report-access model for Developer/Tester roles and additional advanced operational features.

---

## Intended Use

This project can be used as:

- A Django portfolio project
- An academic software project reference
- A demonstration of RBAC and CRUD application design
- A foundation for further DevOps/cloud deployment work
- A practical example of project and defect management workflows

---

## Author

**Suryaprakash R**  
Junior DevOps / Cloud-focused Engineer

GitHub: `https://github.com/suryaprakash-r`

LinkedIn: `https://www.linkedin.com/in/suryaprakash-r/`

---

## License

Add your preferred license here before public distribution, such as MIT, Apache-2.0, or an institution/company-specific license.

---

## Acknowledgement

BugTracker v1.0 was developed incrementally with functional validation after each major module and a final responsive and regression validation pass before release.
