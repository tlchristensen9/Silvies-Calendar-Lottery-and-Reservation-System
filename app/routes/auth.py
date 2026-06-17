"""Authentication routes: login, logout, change password, password recovery."""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, make_response
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app import db, mail
from app.models import Member
from app.forms import (LoginForm, ChangePasswordForm, ForgotPasswordForm,
                       ResetPasswordForm, SettingsForm)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        member = Member.query.filter_by(email=form.email.data.lower().strip()).first()
        if member and member.check_password(form.password.data):
            login_user(member, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {member.name}!', 'success')
            response = make_response(redirect(next_page or url_for('main.dashboard')))
            if form.remember_me.data:
                # Remember the email address so it pre-fills on the next visit.
                response.set_cookie('remembered_email', form.email.data.lower().strip(),
                                    max_age=60 * 60 * 24 * 365, httponly=True, samesite='Lax')
            else:
                response.delete_cookie('remembered_email')
            return response
        flash('Invalid email or password.', 'danger')

    # On GET, pre-fill the email field from the remembered-email cookie.
    if request.method == 'GET':
        remembered = request.cookies.get('remembered_email')
        if remembered:
            form.email.data = remembered
            form.remember_me.data = True

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Legacy route — redirects to settings."""
    return redirect(url_for('auth.settings'))


@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm(obj=current_user)

    if form.validate_on_submit():
        # Verify current password first
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/settings.html', form=form)

        # Check email uniqueness
        new_email = form.email.data.lower().strip()
        if new_email != current_user.email:
            existing = Member.query.filter(
                Member.email == new_email,
                Member.id != current_user.id).first()
            if existing:
                flash('Another member already uses that email address.', 'danger')
                return render_template('auth/settings.html', form=form)

        # Apply changes
        current_user.email = new_email
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your settings have been updated.', 'success')
        return redirect(url_for('main.dashboard'))

    # Pre-fill current password field as empty (don't show hash)
    form.current_password.data = ''

    return render_template('auth/settings.html', form=form)


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def _generate_reset_token(email):
    s = _get_serializer()
    return s.dumps(email, salt='password-reset')


def _verify_reset_token(token, max_age=None):
    s = _get_serializer()
    if max_age is None:
        max_age = current_app.config.get('RESET_TOKEN_EXPIRY', 3600)
    try:
        email = s.loads(token, salt='password-reset', max_age=max_age)
        return email
    except (SignatureExpired, BadSignature):
        return None


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        member = Member.query.filter_by(email=email).first()
        # Always show the same message to avoid email enumeration
        flash('If an account with that email exists, a password reset link has been sent.', 'info')
        if member:
            token = _generate_reset_token(member.email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            try:
                msg = Message(
                    subject='Silvies Club — Password Reset',
                    recipients=[member.email],
                    body=f'Hi {member.name},\n\n'
                         f'You requested a password reset for your Silvies Club account.\n\n'
                         f'Click this link to reset your password:\n{reset_url}\n\n'
                         f'This link expires in 1 hour.\n\n'
                         f'If you did not request this, you can ignore this email.\n\n'
                         f'— Silvies Club Reservation System'
                )
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(f'Failed to send reset email: {e}')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    email = _verify_reset_token(token)
    if not email:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    member = Member.query.filter_by(email=email).first()
    if not member:
        flash('Account not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        member.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)
