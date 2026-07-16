

from datetime import date
import datetime
import uuid

from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_wtf import CSRFProtect
from sqlalchemy import cast, or_
from sqlalchemy.types import String
from urllib.parse import urlparse
from werkzeug.utils import secure_filename

from config import Config
from forms import (
    ApplicationStatusForm,
    CompanyRegistrationForm,
    DriveForm,
    StudentProfileForm,
    StudentRegistrationForm,
    LoginForm,
)
from models import (
    Application,
    CompanyProfile,
    ConfiguredDatabase,
    PlacementDrive,
    StudentProfile,
    User,
    db,
)

login_manager = LoginManager()
login_manager.login_view = "login"
csrf = CSRFProtect()


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash("Access denied. Please log in with the correct account.", "warning")
                return redirect(url_for("login"))
            if not current_user.is_active:
                flash("Your account is deactivated. Contact the institute.", "danger")
                return redirect(url_for("login"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


admin_required = role_required("admin")
company_required = role_required("company")
student_required = role_required("student")


def save_resume_file(file_storage):
    if not file_storage or file_storage.filename == "":
        return None
    filename = secure_filename(file_storage.filename)
    if "." not in filename:
        return None
    extension = filename.rsplit(".", 1)[-1].lower()
    if extension not in Config.ALLOWED_RESUME_EXTENSIONS:
        return None
    upload_path = Path(current_app.config["UPLOAD_FOLDER"])
    upload_path.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{filename}"
    target = upload_path / stored_name
    file_storage.save(target)
    return stored_name


def allowed_to_login(user):
    if not user:
        return False, "No account matched that email."
    profile = user.student_profile or user.company_profile
    if user.role == "company" and profile:
        if profile.approval_status != "Approved":
            return False, "Company profile is awaiting approval."
        if profile.is_blacklisted:
            return False, "This company has been blacklisted."
    if user.role == "student" and profile and profile.is_blacklisted:
        return False, "This student account is blacklisted."
    if not user.is_active:
        return False, "Account is currently deactivated."
    return True, None


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    ConfiguredDatabase.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
        Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
        ConfiguredDatabase.create_all()
        User.ensure_admin()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    def role_dashboard(role):
        if role == "admin":
            return url_for("admin_dashboard")
        if role == "company":
            return url_for("company_dashboard")
        return url_for("student_dashboard")

    @app.route("/")
    def index():
        stats = {
            "students": StudentProfile.query.count(),
            "companies": CompanyProfile.query.count(),
            "drives": PlacementDrive.query.count(),
            "applications": Application.query.count(),
        }
        pending = {
            "companies": CompanyProfile.query.filter_by(approval_status="Pending").count(),
            "drives": PlacementDrive.query.filter_by(status="Pending").count(),
        }
        recent_drives = (
            PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).limit(4).all()
        )
        return render_template(
            "index.html", stats=stats, pending=pending, recent_drives=recent_drives
        )

    @app.route("/auth/login", methods=["GET", "POST"])
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(role_dashboard(current_user.role))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user and user.check_password(form.password.data):
                allowed, message = allowed_to_login(user)
                if not allowed:
                    flash(message, "warning")
                else:
                    login_user(user)
                    flash("Welcome back!", "success")
                    target = request.args.get("next")
                    if target and urlparse(target).netloc == "":
                        return redirect(target)
                    return redirect(role_dashboard(user.role))
            else:
                flash("Invalid credentials.", "danger")
        return render_template("login.html", form=form)

    @app.route("/auth/logout")
    @login_required
    def logout():
        logout_user()
        flash("Signed out successfully.", "info")
        return redirect(url_for("login"))

    @app.route("/student/register", methods=["GET", "POST"])
    def student_register():
        if current_user.is_authenticated:
            return redirect(role_dashboard(current_user.role))
        form = StudentRegistrationForm()
        if form.validate_on_submit():
            existing = User.query.filter_by(email=form.email.data.lower()).first()
            if existing:
                flash("Email already registered.", "danger")
            else:
                user = User(
                    email=form.email.data.lower(),
                    full_name=form.full_name.data,
                    role="student",
                )
                user.password = form.password.data
                db.session.add(user)
                db.session.flush()
                resume_name = save_resume_file(form.resume.data)
                student = StudentProfile(
                    user_id=user.id,
                    branch=form.branch.data,
                    graduation_year=form.graduation_year.data,
                    mobile=form.mobile.data,
                    resume_filename=resume_name,
                )
                db.session.add(student)
                db.session.commit()
                flash("Student account created. Please log in.", "success")
                return redirect(url_for("login"))
        return render_template("student/register.html", form=form)

    @app.route("/company/register", methods=["GET", "POST"])
    def company_register():
        if current_user.is_authenticated:
            return redirect(role_dashboard(current_user.role))
        form = CompanyRegistrationForm()
        if form.validate_on_submit():
            existing = User.query.filter_by(email=form.email.data.lower()).first()
            if existing:
                flash("Email already registered.", "danger")
            else:
                user = User(
                    email=form.email.data.lower(),
                    full_name=form.company_name.data,
                    role="company",
                )
                user.password = form.password.data
                db.session.add(user)
                db.session.flush()
                company = CompanyProfile(
                    user_id=user.id,
                    name=form.company_name.data,
                    hr_contact=form.hr_contact.data,
                    website=form.website.data,
                    description=form.description.data,
                    approval_status="Pending",
                )
                db.session.add(company)
                db.session.commit()
                flash(
                    "Company registered. Await admin approval before logging in.",
                    "success",
                )
                return redirect(url_for("login"))
        return render_template("company/register.html", form=form)

    @app.route("/student/dashboard")
    @student_required
    def student_dashboard():
        profile = current_user.student_profile
        d = "27/02/2026"
        if not profile:
            flash("Complete your profile first.", "warning")
            return redirect(url_for("student_profile"))
        approved_drives = (
            PlacementDrive.query.filter_by(status="Approved")
            .filter(PlacementDrive.application_deadline >= date.today())
            .order_by(PlacementDrive.application_deadline)
            .all()
        )
        applied_ids = {application.drive_id for application in profile.applications}
        history = sorted(
            profile.applications, key=lambda item: item.application_date, reverse=True
        )
        return render_template(
            "student/dashboard.html",
            profile=profile,
            available_drives=approved_drives,
            applied_ids=applied_ids,
            history=history,
            date = d
            
        )

    @app.route("/student/profile", methods=["GET", "POST"])
    @student_required
    def student_profile():
        profile = current_user.student_profile
        form = StudentProfileForm(obj=profile)
        if form.validate_on_submit():
            profile.branch = form.branch.data
            profile.graduation_year = form.graduation_year.data
            profile.mobile = form.mobile.data
            profile.placement_history = form.placement_history.data
            if form.resume.data:
                resume_name = save_resume_file(form.resume.data)
                if resume_name:
                    profile.resume_filename = resume_name
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("student_profile"))
        return render_template("student/profile.html", form=form, profile=profile)

    @csrf.exempt
    @app.route("/student/drives/<int:drive_id>/apply", methods=["POST"])
    @student_required
    def student_apply(drive_id):
        profile = current_user.student_profile
        drive = PlacementDrive.query.get_or_404(drive_id)
        if drive.status != "Approved":
            flash("Cannot apply to unapproved drives.", "danger")
            return redirect(url_for("student_dashboard"))
        if drive.application_deadline < date.today():
            flash("The application window has closed.", "warning")
            return redirect(url_for("student_dashboard"))
        existing = Application.query.filter_by(
            student_id=profile.id, drive_id=drive.id
        ).first()
        if existing:
            flash("You have already applied for this drive.", "info")
            return redirect(url_for("student_dashboard"))
        application = Application(student_id=profile.id, drive_id=drive.id)
        db.session.add(application)
        db.session.commit()
        flash("Application submitted.", "success")
        return redirect(url_for("student_dashboard"))

    @app.route("/company/dashboard")
    @company_required
    def company_dashboard():
        profile = current_user.company_profile
        if not profile:
            flash("Complete your company profile first.", "warning")
            return redirect(url_for("logout"))
        drives = sorted(profile.drives, key=lambda d: d.created_at, reverse=True)
        applicant_count = sum(len(d.applications) for d in drives)
        return render_template(
            "company/dashboard.html",
            profile=profile,
            drives=drives,
            applicant_count=applicant_count,
        )

    @app.route("/company/drives/create", methods=["GET", "POST"])
    @company_required
    def company_create_drive():
        profile = current_user.company_profile
        if profile.approval_status != "Approved" or profile.is_blacklisted:
            flash("Approved companies only can create drives.", "danger")
            return redirect(url_for("company_dashboard"))
        form = DriveForm()
        if form.validate_on_submit():
            drive = PlacementDrive(
                company_id=profile.id,
                job_title=form.job_title.data,
                job_description=form.job_description.data,
                eligibility=form.eligibility.data,
                application_deadline=form.application_deadline.data,
                location=form.location.data,
                salary=form.salary.data,
                status="Pending",
            )
            db.session.add(drive)
            db.session.commit()
            flash("Placement drive created. Await admin approval.", "success")
            return redirect(url_for("company_dashboard"))
        return render_template("company/drive_form.html", form=form, action="Create")

    @app.route("/company/drives/<int:drive_id>/edit", methods=["GET", "POST"])
    @company_required
    def company_edit_drive(drive_id):
        profile = current_user.company_profile
        drive = PlacementDrive.query.filter_by(company_id=profile.id, id=drive_id).first_or_404()
        if drive.status == "Closed":
            flash("Closed drives cannot be edited.", "warning")
            return redirect(url_for("company_dashboard"))
        form = DriveForm(obj=drive)
        if form.validate_on_submit():
            drive.job_title = form.job_title.data
            drive.job_description = form.job_description.data
            drive.eligibility = form.eligibility.data
            drive.application_deadline = form.application_deadline.data
            drive.location = form.location.data
            drive.salary = form.salary.data
            db.session.commit()
            flash("Drive updated.", "success")
            return redirect(url_for("company_dashboard"))
        return render_template("company/drive_form.html", form=form, action="Update")

    @csrf.exempt
    @app.route("/company/drives/<int:drive_id>/close", methods=["POST"])
    @company_required
    def company_close_drive(drive_id):
        profile = current_user.company_profile
        drive = PlacementDrive.query.filter_by(company_id=profile.id, id=drive_id).first_or_404()
        drive.status = "Closed"
        db.session.commit()
        flash("Drive closed.", "info")
        return redirect(url_for("company_dashboard"))

    @app.route("/company/drives/<int:drive_id>/applications")
    @company_required
    def company_drive_applications(drive_id):
        profile = current_user.company_profile
        drive = PlacementDrive.query.filter_by(company_id=profile.id, id=drive_id).first_or_404()
        status_form = ApplicationStatusForm()
        return render_template(
            "company/applications.html", drive=drive, status_form=status_form
        )

    @csrf.exempt
    @app.route("/company/applications/<int:application_id>/status", methods=["POST"])
    @company_required
    def company_update_application(application_id):
        application = Application.query.get_or_404(application_id)
        if application.drive.company.user_id != current_user.id:
            flash("Access denied.", "danger")
            return redirect(url_for("company_dashboard"))
        form = ApplicationStatusForm()
        if form.validate_on_submit():
            application.status = form.status.data
            db.session.commit()
            flash("Application status updated.", "success")
        return redirect(
            url_for("company_drive_applications", drive_id=application.drive_id)
        )

    @app.route("/admin/dashboard")
    @admin_required
    def admin_dashboard():
        stats = {
            "students": StudentProfile.query.count(),
            "companies": CompanyProfile.query.count(),
            "drives": PlacementDrive.query.count(),
            "applications": Application.query.count(),
        }
        pending_companies = CompanyProfile.query.filter_by(approval_status="Pending").all()
        pending_drives = PlacementDrive.query.filter_by(status="Pending").all()
        recent_applications = (
            Application.query.order_by(Application.application_date.desc()).limit(6).all()
        )
        return render_template(
            "admin/dashboard.html",
            stats=stats,
            pending_companies=pending_companies,
            pending_drives=pending_drives,
            recent_applications=recent_applications,
        )

    @app.route("/admin/companies")
    @admin_required
    def admin_companies():
        query = request.args.get("q", "").strip()
        companies = CompanyProfile.query.join(User)
        if query:
            pattern = f"%{query}%"
            companies = companies.filter(
                or_(
                    CompanyProfile.name.ilike(pattern),
                    User.full_name.ilike(pattern),
                    cast(User.id, String).ilike(pattern),
                )
            )
        companies = companies.order_by(CompanyProfile.approval_status).all()
        return render_template("admin/companies.html", companies=companies, query=query)

    @csrf.exempt
    @app.route("/admin/companies/<int:company_id>/status", methods=["POST"])
    @admin_required
    def admin_update_company(company_id):
        company = CompanyProfile.query.get_or_404(company_id)
        action = request.form.get("action")
        if action == "approve":
            company.approval_status = "Approved"
            company.user.is_active = True
            flash(f"{company.name} approved.", "success")
        elif action == "reject":
            company.approval_status = "Rejected"
            company.user.is_active = False
            flash(f"{company.name} rejected.", "warning")
        elif action == "blacklist":
            company.is_blacklisted = not company.is_blacklisted
            state = "blacklisted" if company.is_blacklisted else "removed from blacklist"
            flash(f"{company.name} {state}.", "info")
        db.session.commit()
        return redirect(url_for("admin_companies"))

    @app.route("/admin/students")
    @admin_required
    def admin_students():
        query = request.args.get("q", "").strip()
        students = StudentProfile.query.join(User)
        if query:
            pattern = f"%{query}%"
            students = students.filter(
                or_(
                    User.full_name.ilike(pattern),
                    User.email.ilike(pattern),
                    StudentProfile.mobile.ilike(pattern),
                    cast(User.id, String).ilike(pattern),
                )
            )
        students = students.order_by(User.full_name).all()
        return render_template("admin/students.html", students=students, query=query)

    @csrf.exempt
    @app.route("/admin/students/<int:student_id>/status", methods=["POST"])
    @admin_required
    def admin_update_student(student_id):
        student = StudentProfile.query.get_or_404(student_id)
        action = request.form.get("action")
        if action == "blacklist":
            student.is_blacklisted = not student.is_blacklisted
            state = "blacklisted" if student.is_blacklisted else "removed from blacklist"
            flash(f"{student.user.full_name} {state}.", "info")
        elif action == "deactivate":
            student.user.is_active = False
            flash(f"{student.user.full_name} deactivated.", "warning")
        elif action == "activate":
            student.user.is_active = True
            flash(f"{student.user.full_name} activated.", "success")
        db.session.commit()
        return redirect(url_for("admin_students"))

    @app.route("/admin/drives")
    @admin_required
    def admin_drives():
        drives = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
        return render_template("admin/drives.html", drives=drives)

    @csrf.exempt
    @app.route("/admin/drives/<int:drive_id>/status", methods=["POST"])
    @admin_required
    def admin_update_drive(drive_id):
        drive = PlacementDrive.query.get_or_404(drive_id)
        action = request.form.get("action")
        if action == "approve":
            drive.status = "Approved"
            flash(f"{drive.job_title} approved.", "success")
        elif action == "reject":
            drive.status = "Rejected"
            flash(f"{drive.job_title} rejected.", "warning")
        elif action == "close":
            drive.status = "Closed"
            flash(f"{drive.job_title} closed.", "info")
        db.session.commit()
        return redirect(url_for("admin_drives"))

    @app.route("/admin/applications")
    @admin_required
    def admin_applications():
        applications = (
            Application.query.order_by(Application.application_date.desc()).all()
        )
        status_form = ApplicationStatusForm()
        return render_template("admin/applications.html", applications=applications, status_form=status_form)

    @csrf.exempt
    @app.route("/admin/applications/<int:application_id>/status", methods=["POST"])
    @admin_required
    def admin_update_application(application_id):
        application = Application.query.get_or_404(application_id)
        form = ApplicationStatusForm()
        if form.validate_on_submit():
            application.status = form.status.data
            db.session.commit()
            flash("Application status updated.", "success")
        return redirect(url_for("admin_applications"))

    @app.route("/resumes/<path:filename>")
    @login_required
    def serve_resume(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.context_processor
    def inject_current_year():
        return {"current_year": date.today().year}

    return app
