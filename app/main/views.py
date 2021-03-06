#! -*- coding:utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,current_app,g
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm,EditProfileAdminForm,PostForm,CommentForm
from .. import db
from ..models import Permission,Role,User,Post,Comment,Category
from ..decorators import admin_required
from flask_sqlalchemy import get_debug_queries

@main.before_app_request
def before_request():
    g.categorys=Category.query.all()
    g.hotpost=Post.query.order_by(Post.visits.desc()).all()

@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown=request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'

@main.route('/', methods=['GET', 'POST'])
def index():
    form=PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post=Post(head=form.head.data,body=form.body.data,author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    page=request.args.get('page',1,type=int)
    pagination=Post.query.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    posts=pagination.items
    return render_template('index.html',form=form,posts=posts,pagination=pagination)

@main.route('/user/<username>')
def user(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user is None:
        abort(404)
    page=request.args.get('page', 1, type=int)
    pagination=user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
    posts=pagination.items
    return render_template('user.html',user=user,posts=posts,pagination=pagination)

@main.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
    post=Post.query.get_or_404(id)
    post.visits+=1
    print 'visit add one'
    form=CommentForm()
    if form.validate_on_submit():
        comment=Comment(body=form.body.data,post=post,author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash(u'你的评论已经发表')
        return redirect(url_for('.post',id=post.id,page=-1))
    page=request.args.get('page',1,type=int)
    if page== -1:
        page=(post.comments.count() - 1)/current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination=post.comments.order_by(Comment.timestamp.asc()).paginate(
        page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments=pagination.items
    return render_template('post.html',posts=[post],form=form,comments=comments,pagination=pagination)

@main.route('/delete_post/<int:id>')
@login_required
def delete_post(id):
    post=Post.query.get_or_404(id)
    if current_user==post.author:
        db.session.delete(post)
        db.session.commit()
        flash(u'文章删除成功')
    return redirect(url_for('main.index'))

@main.route('/category/<int:id>',methods=['GET','POST'])
def category(id):
    category=Category.query.get_or_404(id)
    page=request.args.get('page',1,type=int)
    if page== -1:
        page=(category.posts.count() -1)/ \
            current_app.config['FLASKY_POSTS_PER_PAGE'] + 1
    pagination=category.posts.order_by(Post.timestamp.asc()).paginate(
        page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False
    )
    posts=pagination.items
    return render_template('category.html',category=category,posts=posts,pagination=pagination)

@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
    post=Post.query.get_or_404(id)
    if current_user !=post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.head=form.head.data
        post.body=form.body.data
        post.category=Category.query.get(form.category.data)
        db.session.add(post)
        db.session.commit()
        flash(u'文章已经更新')
        return redirect(url_for('.post',id=post.id))
    form.head.data=post.head
    form.body.data=post.body
    form.category.data=post.category_id
    return render_template('edit_post.html',form=form)

@main.route('/edit-profile',methods=['GET', 'POST'])
@login_required
def edit_profile():
    form=EditProfileForm()
    if form.validate_on_submit():
        current_user.name=form.name.data
        current_user.location=form.location.data
        current_user.about_me=form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash(u'你的个人资料已经更新')
        return redirect(url_for('.user',username=current_user.username))
    form.name.data=current_user.name
    form.location.data=current_user.location
    form.about_me.data=current_user.about_me
    return render_template('edit_profile.html',form=form)

@main.route('/edit-profile/<int:id>', methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user=User.query.get_or_404(id)
    form=EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email=form.email.data
        user.username=form.username.data
        user.confirmed=form.confirmed.data
        user.role=Role.query.get(form.role.data)
        user.name=form.name.data
        user.location=form.location.data
        user.about_me=form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user',username=user.username))
    form.email.data=user.email
    form.username.data=user.username
    form.confirmed.data=user.confirmed
    form.role.data=user.role_id
    form.name.data=user.name
    form.location.data=user.location
    form.about_me.data=user.about_me
    return render_template('edit_profile.html',form=form,user=user)

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query:%s\nParameters:%s\nDuration:%fs\nContext:%s\n'%
                (query.statement,query.parameters,query.duration,query.context)
            )
    return response

@main.route('/new-article', methods=['GET','POST'])
@login_required
def new_article():
    form=PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post=Post(
            head=form.head.data,
            body=form.body.data,
            category=Category.query.get(form.category.data),
            author=current_user._get_current_object(),
        )
        db.session.add(post)
        db.session.commit()
        flash(u'新文章发布成功')
        return redirect(url_for('.post',id=post.id))
    return render_template('new_article.html',form=form)



