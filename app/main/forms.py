#! -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import SubmitField,StringField,TextAreaField,BooleanField,SelectField
from wtforms.validators import DataRequired,Length,Email,Regexp
from wtforms import ValidationError
from ..models import User,Role,Category
from flask_pagedown.fields import PageDownField

class NameForm(FlaskForm):
    name=StringField(u'你的名字?',[DataRequired()])
    submit=SubmitField(u'确认')

class EditProfileForm(FlaskForm):
    name=StringField(u'昵称：',validators=[Length(0,64)])
    location=StringField(u'地址：',validators=[Length(0,64)])
    about_me=TextAreaField(u'关于我：')
    submit=SubmitField(u'确认')

class EditProfileAdminForm(FlaskForm):
    email=StringField(u'电子邮箱：',validators=[DataRequired(),Length(1,64),Email()])
    username=StringField(u'用户名：',validators=[
        DataRequired(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,
                         'Usernames must have only letters,'
                         'numbers,dots or underscores')])
    confirmed=BooleanField(u'确认')
    role=SelectField(u'角色：',coerce=int)
    name=StringField(u'真实姓名：',validators=[Length(0, 64)])
    location=StringField(u'地址：',validators=[Length(0, 64)])
    about_me=TextAreaField(u'关于我：')
    submit=SubmitField(u'确认')

    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        self.role.choices=[(role.id,role.name)
                           for role in Role.query.order_by(Role.name).all()]
        self.user=user

    def validate_email(self,field):
        if field.data!=self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError(u'电子邮箱已经被注册')

    def validate_username(self,field):
        if field.data!=self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError(u'用户已被占用')

class PostForm(FlaskForm):
    head=StringField(u'文章标题',validators=[DataRequired()])
    body=PageDownField(u'文章正文',validators=[DataRequired()])
    category=SelectField(u'文章分类',coerce=int)
    submit=SubmitField(u'发布')

    def __init__(self,*args,**kwargs):
        super(PostForm,self).__init__(*args,**kwargs)
        self.category.choices=[(category.id,category.category)
                           for category in Category.query.order_by(Category.category).all()]

class CommentForm(FlaskForm):
    body=StringField(u'输入你的评论',validators=[DataRequired()])
    submit=SubmitField(u'确认')









