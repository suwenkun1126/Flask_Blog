#! -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import DataRequired,Length,Email,Regexp,EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(FlaskForm):
    email=StringField(u'邮箱',validators=[DataRequired(),Length(1,64),Email()])
    password=PasswordField(u'密码',validators=[DataRequired()])
    remember_me=BooleanField(u'记住我')
    submit=SubmitField(u'登入')

class RegistrationForm(FlaskForm):
    email=StringField(u'邮箱',validators=[DataRequired(),Length(1,64),Email()])
    username=StringField(u'用户名',validators=[
        DataRequired(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,
                                           u'用户名必须为字母,'
                                           u'数字，点或下划线')])
    password=PasswordField(u'密码',validators=[
        DataRequired(),EqualTo(u'确认密码',message=u'密码必须一致')])
    password2=PasswordField(u'确认密码',validators=[DataRequired()])
    submit=SubmitField(u'注册')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮箱已被注册')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'用户名已存在')

class  ChangePasswordForm(FlaskForm):
    oldpassword=PasswordField(u'旧密码',validators=[DataRequired()])
    password=PasswordField(u'新密码', validators=[
                DataRequired(), EqualTo(u'确认新密码', message=u'密码必须一致')])
    password2=PasswordField(u'确认新密码',validators=[DataRequired()])
    submit=SubmitField(u'更改密码')
