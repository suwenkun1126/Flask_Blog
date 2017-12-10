#! -*- coding:utf-8 -*-
from flask import render_template,redirect,request,url_for,flash
from flask_login import login_user,logout_user,login_required
from . import auth
from .. import db
from ..models import User
from ..email import send_email
from .forms import LoginForm,RegistrationForm,ChangePasswordForm
from flask_login import current_user

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5]!='auth.':
           return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user,form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash(u'用户名或密码不正确')
    return render_template('auth/login.html',form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'账号成功注销')
    return redirect(url_for('main.index'))

@auth.route('/register',methods=['GET','POST'])
def register():
    form=RegistrationForm()
    if form.validate_on_submit():
        user=User(email=form.email.data,
                  username=form.username.data,
                  password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token=user.generate_confirmation_token()
        send_email(user.email,'Confirm Your Account',
                   'auth/email/confirm',user=user,token=token)
        flash(u'确认邮件已发送至您的邮箱')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html',form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash(u'确认账号成功，谢谢！')
    else:
        flash(u'确认链接非法或者已经失效')
    return redirect(url_for('main.index'))

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token=current_user.generate_confirmation_token()
    send_email(current_user.email,'Confirm Your Account',
               'auth/email/confirm',user=current_user,token=token)
    flash(u'新的确认邮件已发送至您的邮箱')
    return redirect(url_for('main.index'))

@auth.route('/change-password',methods=['GET','POST'])
@login_required
def change_password():
    form=ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.oldpassword.data):
            current_user.password=form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash(u'密码更改成功')
            return redirect(url_for('main.index'))
        else:
            flash(u'密码错误')
    return render_template("auth/change-password.html",form=form)


















