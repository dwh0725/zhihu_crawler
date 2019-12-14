#!/usr/bin/python
# -*- coding : utf-8 -*-

"""                                                   
File: services.py
Author: dwh
E-mail: dwh@bupt.edu.cn
Created: 2019/11/13 18:47
Description:                                              
"""

from sqlalchemy import create_engine, cast, Date
from sqlalchemy.orm import sessionmaker, scoped_session
from models import UserInfo
import datetime


class MySQLServices(object):
    uri = 'mysql+pymysql://{}:{}@{}:3306/zhihu'.format('username', 'password', 'mysql_address')
    engine = create_engine(uri)
    ins = sessionmaker(engine)

    @classmethod
    def insert(cls, session, item):
        session.add(item)
        session.commit()

    @classmethod
    def bulk_insert(cls, session, items):
        session.bulk_save_objects(items)
        session.commit()

    @classmethod
    def get_one(cls, session, table_name, **kwargs):
        res = session.query(table_name).filter_by(**kwargs).one_or_none()
        return res

    @classmethod
    def close(cls):
        cls.engine.dispose()

