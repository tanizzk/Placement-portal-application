from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(140))
    role = db.Column(db.String(32), default="student")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_profile = db.relationship(
        "StudentProfile", back_populates="user", uselist=False
    )
    company_profile = db.relationship(
        "CompanyProfile", back_populates="user", uselist=False
    )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_student(self):
        return self.role == "student"

    @property
    def is_company(self):
        return self.role == "company"

    @classmethod
    def ensure_admin(cls):
        if not Config.ADMIN_EMAIL or not Config.ADMIN_PASSWORD:
            return
        admin = (
            cls.query.filter_by(email=Config.ADMIN_EMAIL, role="admin").first()
        )
        if admin:
            return
        admin = cls(
            email=Config.ADMIN_EMAIL,
            full_name="Placement Admin",
            role="admin",
        )
        admin.password = Config.ADMIN_PASSWORD
        db.session.add(admin)
        db.session.commit()


class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    branch = db.Column(db.String(120))
    graduation_year = db.Column(db.Integer)
    mobile = db.Column(db.String(20))
    resume_filename = db.Column(db.String(255))
    placement_history = db.Column(db.Text)
    is_blacklisted = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="student_profile")
    applications = db.relationship("Application", back_populates="student")

    def latest_status(self):
        if not self.applications:
            return "No applications yet"
        latest = max(self.applications, key=lambda app: app.application_date)
        return latest.status


class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    name = db.Column(db.String(180), nullable=False)
    hr_contact = db.Column(db.String(120))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    approval_status = db.Column(db.String(32), default="Pending")
    is_blacklisted = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="company_profile")
    drives = db.relationship("PlacementDrive", back_populates="company")


class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company_profile.id"))
    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility = db.Column(db.Text)
    application_deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), default="Pending")
    location = db.Column(db.String(150))
    salary = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship("CompanyProfile", back_populates="drives")
    applications = db.relationship("Application", back_populates="drive")

    @property
    def applicant_count(self):
        return len(self.applications)

    @property
    def is_active(self):
        return self.status == "Approved"


class Application(db.Model):
    __tablename__ = "application"
    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="u_student_drive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"))
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drive.id"))
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(
        db.String(32), default="Applied"
    )  # Applied / Shortlisted / Selected / Rejected
    remarks = db.Column(db.Text)

    student = db.relationship("StudentProfile", back_populates="applications")
    drive = db.relationship("PlacementDrive", back_populates="applications")


class ConfiguredDatabase:
    @staticmethod
    def init_app(app):
        db.init_app(app)

    @staticmethod
    def create_all():
        db.create_all()
