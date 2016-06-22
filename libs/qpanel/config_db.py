# -*- coding: utf-8 -*-

#
# Copyright (C) 2015-2016 Rodrigo Ramírez Norambuena <a@rodrigoramirez.com>
#
import os
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func
import hashlib
import settings
import utils

HERE = os.path.abspath(os.path.dirname(__file__))
PATH_DB = os.path.join(HERE, os.pardir, os.pardir, 'data', 'database.db')
engine = create_engine('sqlite:///' + PATH_DB, echo=True)

# session
session_dbconfig = scoped_session(sessionmaker(bind=engine,
                                               autoflush=False,
                                               autocommit=False))

DeclarativeBase = declarative_base()
metadata = MetaData()


class Config(DeclarativeBase):

    __tablename__ = "config"

    id = Column(Integer, primary_key=True)
    namespace = Column(String)
    setting = Column(String)
    value = Column(String)

    def __init__(self, namespace, setting, value):
        self.namespace = namespace
        self.setting = setting
        self.value = value

    @staticmethod
    def add_data(*args, **kw):
        parse_config_to_db()


class User(DeclarativeBase):

    __tablename__ = "user"

    username = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)

    query = session_dbconfig.query_property()

    def __init__(self, username, password):
        m = hashlib.md5()
        m.update(password)
        self.username = username
        self.password = m.hexdigest()

    def as_dict(self):
        return {'name': self.name, 'username': self.username,
                'email': self.email}

    @staticmethod
    def count():
        return session_dbconfig.query(func.count(User.username)).scalar()

    @staticmethod
    def get_by_username(username):
        return session_dbconfig.query(User).\
                filter(User.username == username).first()

    @staticmethod
    def valid_user(username, password):
        user = User.get_by_username(username)
        if not user:
            return False
        if user.password == utils.to_md5(password):
            return True
        return False


def parse_config_to_db():
    """
        Parser config file and add into config database
    """
    config_file = utils.open_config_ini_file(settings.PATH_FILE_CONFIG)
    sections = config_file.sections()
    for s in sections:
        items = dict(config_file.items(s))
        for i in items:
            value = config_file.get(s, i)
            if s == 'users':
                new_cfg = User(i, value)
            else:
                new_cfg = Config(s, i, value)
            session_dbconfig.add(new_cfg)
            session_dbconfig.commit()


event.listen(User.__table__, "after_create", Config.add_data)
DeclarativeBase.metadata.create_all(engine)
