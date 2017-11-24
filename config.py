import os
basedir=os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY=os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN=True
    SQLALCHEMY_TRACK_MODIFICATIONS=True
    FLASKY_MAIL_SUBJECT_PREFIX='[Flasky]'
    FLASKY_MAIL_SENDER='378733604@qq.com'
    FLASKY_ADMIN=os.environ.get('FLASKY_ADMIN')
    # FLASKY_ADMIN='378733604@qq.com'
    FLASKY_COMMENTS_PER_PAGE=10
    FLASKY_POSTS_PER_PAGE=10
    SQLCHEMY_RECORD_QUERIES=True
    FLASKY_SLOW_DB_QUERY_TIME=0.5

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG=True
    MAIL_SERVER='smtp.qq.com'
    MAIL_PORT=465
    MAIL_USE_TLS=False
    MAIL_USE_SSL=True
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME')
    # MAIL_USERNAME='37xxxxxxx@qq.com'
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD')
    # MAIL_PASSWORD='kvxxxxxxxxxxxx'
    # SQLALCHEMY_DATABASE_URI=os.environ.get('DEV_DATABASE_URL') or \
    #     'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    SQLALCHEMY_DATABASE_URI=os.environ.get('DEV_DATABASE_URL')

class TestingConfig(Config):
    TESTING=True
    WTF_CSRF_ENABLED=False
    # SQLALCHEMY_DATABASE_URI=os.environ.get('TEST_DATABASE_URL') or \
    #     'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    SQLALCHEMY_DATABASE_URI=os.environ.get('TEST_DATABASE_URL')

class ProductionConfig(Config):
    # SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or \
    #                           'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    MAIL_SERVER='smtp.qq.com'
    MAIL_PORT=465
    MAIL_USE_TLS=False
    MAIL_USE_SSL=True
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL')
    @classmethod
    def init_app(cls,app):
        Config.init_app(app)

        import logging
        from logging.handlers import SMTPHandler
        credentials=None
        secure=None
        if getattr(cls,'MAIL_USERNAME',None) is not None:
            credentials=(cls.MAIL_USERNAME,cls.MAIL_PASSWORD)
            if getattr(cls,'MAIL_USE_TLS',None):
                secure=()
        mail_handler=SMTPHandler(
            mailhost=(cls.MAIL_SERVER,cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX+'Application Error',
            credentials=credentials,
            secure=secure
             )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

config={
    'development':DevelopmentConfig,
    'testing':TestingConfig,
    'production':ProductionConfig,

    'default':DevelopmentConfig}
