# Placement Portal Application

A multi-role placement management system built with Flask, Jinja2, Bootstrap, and SQLite. The application lets administrators manage companies, placement drives, and students, while companies publish drives and view applications and students keep track of drives and application status.

## Features
- Role-based access for Admin, Company, and Student accounts.
- Admin dashboard with key totals, pending approvals, and full control over companies, drives, and applications.
- Company registration, approval workflow, drive creation, applicant shortlisting, and closing drives.
- Student registration, resume upload, approved drive browsing, one-time applications, and status tracking.
- Programmatic SQLite schema creation with seeded admin credentials specified in the config or environment.

## Tech Stack
- **Backend:** Flask, Flask-Login, Flask-WTF, SQLAlchemy
- **Frontend:** Jinja2 templates, Bootstrap 5, custom CSS
- **Database:** SQLite (managed via `instance/placement_portal.db`)

## Setup
1. Install dependencies (recommend inside a virtual environment):
  
   pip install -r requirements.txt
  
2. Ensure the centralized upload folder exists (it is created automatically when the app starts).
3. Launch the application:
   
   flask --app app:create_app run

4. The default admin user credentials live in environment variables `ADMIN_EMAIL` / `ADMIN_PASSWORD`. Defaults are `admin@placement.local` and `placement123`.

## Folder Layout
```
placement_portal/
├── app.py                  # Flask application factory + routes
├── models.py               # SQLAlchemy schema for users, companies, drives, applications
├── forms.py                # Flask-WTF forms for login, registrations, drives, profiles
├── config.py               # Configuration and upload path settings
├── templates/              # Jinja2 templates organized by role (admin, company, student)
├── static/css/site.css     # Custom UI styling
├── instance/               # Database file and resume uploads
└── README.md               # This file
```

## Usage Notes
- Admins must exist ahead of time; they validate and approve companies/drives before companies can proceed.
- Students can upload resumes, edit their profile, view approved drives, and apply once per drive.
- Companies can create drives only after receiving approval and can update application statuses.
- All data (users, drives, applications) persist inside the SQLite database created under `instance/placement_portal.db`.

## Submission Guidelines
Package the entire project root into a ZIP (`projectname_2XfX00XXXX.zip`) so that unzipping preserves this structure. Include the `templates/`, `static/`, `instance/`, and application files before submitting.
# Placement Portal – Web Based Placement Management System

## Author

Name: Tanishk S Nair
Roll Number: 23f3004469
Email: [23f3004469@ds.study.iitm.ac.in](mailto:23f3004469@ds.study.iitm.ac.in)
Program: BS in Data Science and Applications
Institution: IIT Madras

---

## Project Description

Placement Portal is a web-based application designed to streamline and manage the campus recruitment process. The system provides a centralized platform where students can view job opportunities posted by companies and apply for suitable roles.

Administrators can manage company details, create job postings, and track student applications through a dashboard. The portal improves transparency in the recruitment process and reduces the manual work involved in managing campus placements.

The application is developed using Python and Flask with database integration to store user data, job postings, and application records.

---

## Key Features

### Student Features

* Student registration and login
* View available companies and job opportunities
* Apply for job roles
* Track application status

### Admin Features

* Admin login
* Add and manage companies
* Post job opportunities
* View student applications
* Monitor placement statistics

---

## System Modules

### 1. Authentication Module

Handles user registration and login functionality for students and administrators.

### 2. Company Management Module

Allows administrators to add, update, and manage company details and recruitment drives.

### 3. Job Posting Module

Enables administrators to create and manage job opportunities offered by companies.

### 4. Application Module

Allows students to apply for jobs and track the status of their applications.

### 5. Dashboard Module

Provides an overview of applications, job postings, and placement statistics.

---

## Technologies Used

Frontend

* HTML
* CSS
* Bootstrap

Backend

* Python
* Flask

Database

* SQLite

Libraries

* Chart.js (for data visualization)

---

## Project Structure

```
placement-portal/
│
├── app.py
├── models.py
├── requirements.txt
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│
├── static/
│   ├── css/
│   ├── js/
│
└── README.md
```

---

## How to Run the Project

1. Clone the repository

```
git clone https://github.com/your-repository/placement-portal.git
```

2. Navigate to the project folder

```
cd placement-portal
```

3. Install dependencies

```
pip install -r requirements.txt
```

4. Run the application

```
python app.py
```

5. Open the browser and visit

```
http://127.0.0.1:5000
```

---




