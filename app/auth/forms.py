from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import DataRequired,Length,Email,Regexp,EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(FlaskForm):
    email=StringField('Email',validators=[DataRequired(),Length(1,64),Email()])
    password=PasswordField('Password',validators=[DataRequired()])
    remember_me=BooleanField('Keep me login in')
    submit=SubmitField('Log In')

class RegistrationForm(FlaskForm):
    email=StringField('Email',validators=[DataRequired(),Length(1,64),Email()])
    username=StringField('Username',validators=[
        DataRequired(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,
                                           'Username must have only letters,'
                                           'numbers,dots or underscores')])
    password=PasswordField('Password',validators=[
        DataRequired(),EqualTo('password2',message='Password must match.')])
    password2=PasswordField('Confirm password',validators=[DataRequired()])
    submit=SubmitField('Register')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email has already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use')

class  ChangePasswordForm(FlaskForm):
    oldpassword=PasswordField('Old password',validators=[DataRequired()])
    password=PasswordField('New password', validators=[
                DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2=PasswordField('Confirm password',validators=[DataRequired()])
    submit=SubmitField('Update Password')
