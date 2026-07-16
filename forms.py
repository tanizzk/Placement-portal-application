from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)
from email_validator import EmailNotValidError, validate_email


def flexible_email(form, field):
    if not field.data:
        raise ValidationError("Email is required.")
    try:
        validate_email(field.data, check_deliverability=False)
    except EmailNotValidError as exc:
        domain = field.data.split("@")[-1] if "@" in field.data else ""
        if domain.endswith(".local"):
            return
        raise ValidationError("Invalid email address.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[flexible_email, Length(max=150)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Log In")


class StudentRegistrationForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=140)])
    email = StringField("Email", validators=[flexible_email, Length(max=150)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
    )
    branch = StringField("Branch / Department", validators=[Optional(), Length(max=120)])
    graduation_year = IntegerField(
        "Graduation Year", validators=[Optional(), NumberRange(min=2000, max=2100)]
    )
    mobile = StringField("Mobile Number", validators=[Optional(), Length(max=20)])
    resume = FileField(
        "Upload Resume",
        validators=[Optional(), FileAllowed(["pdf", "doc", "docx"], "Resume must be PDF/DOC/DOCX")],
    )
    submit = SubmitField("Create Student Account")


class CompanyRegistrationForm(FlaskForm):
    company_name = StringField("Company Name", validators=[DataRequired(), Length(max=180)])
    email = StringField("Contact Email", validators=[flexible_email, Length(max=150)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
    )
    hr_contact = StringField("HR Contact Name", validators=[Optional(), Length(max=120)])
    website = StringField("Website", validators=[Optional(), Length(max=200)])
    description = TextAreaField("Company Description", validators=[Optional(), Length(max=800)])
    submit = SubmitField("Register Company")


class DriveForm(FlaskForm):
    job_title = StringField("Job Title", validators=[DataRequired(), Length(max=200)])
    job_description = TextAreaField("Job Description", validators=[DataRequired(), Length(max=2000)])
    eligibility = TextAreaField("Eligibility Criteria", validators=[Optional(), Length(max=1200)])
    application_deadline = DateField("Application Deadline", validators=[DataRequired()])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    salary = StringField("Salary / Stipend", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Save Drive")


class StudentProfileForm(FlaskForm):
    branch = StringField("Branch / Department", validators=[Optional(), Length(max=120)])
    graduation_year = IntegerField(
        "Graduation Year", validators=[Optional(), NumberRange(min=2000, max=2100)]
    )
    mobile = StringField("Mobile Number", validators=[Optional(), Length(max=20)])
    placement_history = TextAreaField("Placement History / Notes", validators=[Optional(), Length(max=1500)])
    resume = FileField(
        "Replace Resume",
        validators=[Optional(), FileAllowed(["pdf", "doc", "docx"], "Resume must be PDF/DOC/DOCX")],
    )
    submit = SubmitField("Update Profile")


class ApplicationStatusForm(FlaskForm):
    status = SelectField(
        "Application Status",
        validators=[DataRequired()],
        choices=[
            ("Applied", "Applied"),
            ("Shortlisted", "Shortlisted"),
            ("Selected", "Selected"),
            ("Rejected", "Rejected"),
        ],
    )
    submit = SubmitField("Update Status")
