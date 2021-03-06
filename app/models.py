#! -*- coding: utf-8 -*-
from datetime import datetime
from werkzeug.security import generate_password_hash,check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app,request,url_for
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager,db
import hashlib
from markdown import markdown
import bleach
from app.exceptions import ValidationError

class Permission:
    FOLLOW=0x01
    COMMENT=0x02
    WRITE_ARTICLES=0x04
    MODERATE_COMMENTS=0x08
    ADMINISTER=0x80

class Role(db.Model):
    __tablename__ = 'roles'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(64), unique=True)
    default=db.Column(db.Boolean,default=False,index=True)
    permissions=db.Column(db.Integer)
    users=db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles={
            'User':(Permission.FOLLOW|
                    Permission.COMMENT|
                    Permission.WRITE_ARTICLES,True),
            'Moderator':(Permission.FOLLOW|
                         Permission.COMMENT|
                         Permission.WRITE_ARTICLES|
                         Permission.MODERATE_COMMENTS,False),
            'Administrator':(0xff,False)
        }
        for r in roles:
            role=Role.query.filter_by(name=r).first()
            if role is None:
                role=Role(name=r)
            role.permissions=roles[r][0]
            role.default=roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

class User(UserMixin,db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(64),unique=True,index=True)
    username=db.Column(db.String(64),unique=True,index=True)
    password_hash=db.Column(db.String(128))
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))
    confirmed=db.Column(db.Boolean,default=False)
    name=db.Column(db.String(64))
    location=db.Column(db.String(64))
    about_me=db.Column(db.TEXT())
    member_since=db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen=db.Column(db.DateTime(),default=datetime.utcnow)
    avatar_hash=db.Column(db.String(32))
    posts=db.relationship('Post',backref='author',lazy='dynamic')
    comments=db.relationship('Comment',backref='author',lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u=User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email==current_app.config['FLASKY_ADMIN']:
                self.role=Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role=Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    def generate_confirmation_token(self,expiration=3600):
        s=Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'confirm':self.id})

    def confirm(self,token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        if data.get('confirm')!=self.id:
            return False
        self.confirmed=True
        db.session.add(self)
        db.session.commit()
        return True

    def can(self,permissions):
        return self.role is not None and \
               (self.role.permissions & permissions)==permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen=datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def change_email(self,token):
        self.email=new_email
        self.avatar_hash=self.gravatar_hash()
        db.session.add(self)
        db.session.commit()
        return True

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self,size=100,default='identicon',rating='g'):
        if request.is_secure:
            url='https://cn.gravatar.com/avatar'
        else:
            url='http://cn.gravatar.com/avatar'
        hash=self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url,hash=hash,size=size,default=default,rating=rating)

    def generate_auth_token(self,expiration):
        s=Serializer(current_app.config['SECRET_KEY'],expires_in=expiration)
        return s.dumps({'id':self.id})

    @staticmethod
    def verify_auth_token(token):
        s=Serializer(current_app.config['SECRECT_KEY'])
        try:
            data=s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def to_json(self):
        json_user={
            'url':url_for('api.get_user',id=self.id,_external=True),
            'username':self.username,
            'member_since':self.member_since,
            'last_since':self.last_seen,
            'posts':url_for('api.get_user_posts',id=self.id,_external=True),
            'post_count':self.posts.count(),
        }
        return json_user

    def __repr__(self):
        return '<User %r>' % self.username

class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False
    def is_administrator(self):
        return False

login_manager.anonymous_user=AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Post(db.Model):
    __tablename__='posts'
    id=db.Column(db.Integer,primary_key=True)
    head=db.Column(db.TEXT)
    body=db.Column(db.TEXT)
    body_html=db.Column(db.TEXT)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    comments=db.relationship('Comment',backref='post',lazy='dynamic')
    category_id=db.Column(db.Integer,db.ForeignKey('category.id'))
    visits=db.Column(db.Integer,server_default="true", nullable=False,default=1)

    @staticmethod
    def generate_fake(count=100):
        from random import seed,randint
        import forgery_py

        seed()
        user_count=User.query.count()
        for i in range(count):
            u=User.query.offset(randint(0, user_count - 1)).first()
            p=Post(
                head=forgery_py.lorem_ipsum.sentences(randint(1,3)),
                body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                timestamp=forgery_py.date.date(True),
                author=u)
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags=['a','abbr','acronym','b','blockquote','code',
                    'em','i','li','ol','pre','strong','ul',
                    'h1','h2','h3','p','center','img']
        attrs={
            '*':['class'],
            'a': ['href', 'rel'],
            'img': ['src', 'alt']
        }
        target.body_html=bleach.linkify(
            bleach.clean(
                markdown(value,output_format='html'),
                tags=allowed_tags,
                strip=True,
                attributes=attrs
            )
        )

    def to_json(self):
        json_post={
            'url':url_for('api.get_post',id=self.id,_external=True),
            'body':self.body,
            'body_html':self.body_html,
            'timestamp':self.timestamp,
            'author':url_for('api.get_user',id=self.author_id,_external=True),
            'comments':url_for('api.get_post_comments',id=self.id,_external=True),
            'comment_count':self.comments.count(),
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body=json_post.get('body')
        if body is None or body=='':
            raise ValidationError('post does not have a body')
        return Post(body=body)

    @staticmethod
    def add_default_head():
        for post in Post.query.all():
            if not post.head:
                post.head=u'其它'
                db.session.add(post)
                db.session.commit()

    @staticmethod
    def add_default_category():
        for post in Post.query.all():
            if not post.category:
                post.category=Category.query.filter_by(category=u'其它').first()
                db.session.add(post)
                db.session.commit()

db.event.listen(Post.body,'set',Post.on_changed_body)

class Comment(db.Model):
    __tablename__='comments'
    id=db.Column(db.Integer,primary_key=True)
    body=db.Column(db.TEXT)
    body_html=db.Column(db.TEXT)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    disabled=db.Column(db.Boolean)
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    post_id=db.Column(db.Integer,db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a','abbr','acronym','b','code',
                        'em','i','strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_comment={
            'url':url_for('api.get_comment',id=self.id),
            'post_url':url_for('api.get_post',id=self.post_id),
            'body':self.body,
            'body_html':self.body_html,
            'timestamp':self.timestamp,
            'author_url':url_for('api.get_user',id=self.author_id),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body=json_comment.get('body')
        if body is None or body=='':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)

db.event.listen(Comment.body,'set',Comment.on_changed_body)

class Category(db.Model):
    __tablename__='category'
    id=db.Column(db.Integer,primary_key=True)
    category=db.Column(db.Unicode(128),unique=True)
    posts=db.relationship('Post',backref='category',lazy='dynamic')

    @staticmethod
    def add_category():
        categorys=[
            u'Web开发',
            u'Python爬虫',
            u'Linux',
            u'Git',
            u'MongoDB数据库',
            u'Redis数据库',
            u'Mysql数据库',
            u'生活感悟',
            u'其它',
            u'数据分析',
            u'服务器',
        ]
        for c in categorys:
            category=Category.query.filter_by(category=c).first()
            if category is None:
                category=Category(category=c)
            db.session.add(category)
        db.session.commit()

    def __repr__(self):
        return '<Category %r>' % self.category













