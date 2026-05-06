"""WTForms for the Silvies Club Reservation System."""

from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                     SelectField, DateField, TextAreaField, IntegerField)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=6, message='Password must be at least 6 characters.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Change Password')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=6, message='Password must be at least 6 characters.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')


class SettingsForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    current_password = PasswordField('Current Password', validators=[DataRequired()],
                                     description='Required to save any changes')
    new_password = PasswordField('New Password (leave blank to keep current)', validators=[
        Optional(), Length(min=6, message='Password must be at least 6 characters.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        Optional(), EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Save Changes')


class ReservationForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=60,
                          message='Notes must be 60 characters or fewer.')])
    submit = SubmitField('Reserve Dates')


class MemberForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    role = SelectField('Role', choices=[
        ('regular', 'Regular Member'),
        ('lifetime', 'Lifetime Member'),
        ('admin', 'Admin (Spike)')
    ])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    submit = SubmitField('Save Member')


class SeasonForm(FlaskForm):
    year = IntegerField('Season Year', validators=[DataRequired(), NumberRange(min=2025, max=2100)])
    phase1_optin_start = DateField('Phase 1 Opt-In Start (e.g., Oct 1)', validators=[Optional()])
    phase1_draft_date = DateField('Phase 1 Draft Date (e.g., Nov 1)', validators=[Optional()])
    phase2_start = DateField('Phase 2 Start (e.g., Jan 1)', validators=[Optional()])
    phase3_start = DateField('Phase 3 Start (e.g., Feb 1)', validators=[Optional()])
    submit = SubmitField('Create Season')


class EditReservationForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=60,
                          message='Notes must be 60 characters or fewer.')])
    submit = SubmitField('Save Changes')


class AdminReservationForm(FlaskForm):
    member_id = SelectField('Member', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=60,
                          message='Notes must be 60 characters or fewer.')])
    is_blocked = BooleanField('Block Dates (e.g., Annual Meeting)')
    block_label = StringField('Block Label', validators=[Optional(), Length(max=100)],
                              description='e.g., "Annual Meeting" — shown on calendar')
    submit = SubmitField('Create Reservation')
