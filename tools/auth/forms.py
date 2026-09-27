from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class RegistrationForm(FlaskForm):
    email = EmailField("Email address", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=12, max=128)])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = EmailField("Email address", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Sign in")
