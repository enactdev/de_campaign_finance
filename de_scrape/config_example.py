import os

class Config(object):
    """
    Base configuration, extended by classes below. 
    """
    VERSION = '0.1.0'
    DEBUG = True
    SSL = False
    SECURITY_TRACKABLE = True
    SECRET_KEY = 'This is not a good secret key.'
    #SECURITY_LOGIN_URL = '/students/login'
    #SECURITY_URL_PREFIX = '/students'

    CONTRIBUTION_CSV_DIRECTORY = '/path/to/csv/files'

    # Flask-Security config
    SECURITY_URL_PREFIX = "/admin"
    SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
    SECURITY_PASSWORD_SALT = "This-is-not-a-good-salt"

    # Flask-Security URLs, overridden because they don't put a / at the end
    #SECURITY_LOGIN_URL = "/login/"
    #SECURITY_LOGOUT_URL = "/logout/"
    #SECURITY_REGISTER_URL = "/register/"

    SECURITY_POST_LOGIN_VIEW = "/admin/"
    #SECURITY_POST_LOGOUT_VIEW = "/admin/"
    #SECURITY_POST_REGISTER_VIEW = "/admin/"

    # Flask-Security features
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False


    DEBUG_TB_INTERCEPT_REDIRECTS = False

    PROPAGATE_EXCEPTIONS = True

    SQLALCHEMY_DATABASE_URI = 'mysql://de_user:de_pass@localhost/de_scrape?charset=utf8&use_unicode=1';
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True


class LocalConfig(Config):
    """
    Config used when running locally
    """
    DEBUG = True
    #TESTING = True

class DevelopmentConfig(Config):
    """
    Config used on the development server. 
    """
    DEBUG = True
    #TESTING = False

class TestingConfig(Config):
    """
    Config used when running tests
    """
    DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    """
    Config used in production. 
    """
    DEBUG = False
    #TESTING = False
