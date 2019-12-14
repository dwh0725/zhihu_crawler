#!/usr/bin/python
# -*- coding : utf-8 -*-

"""                                                   
File: mysql.py
Author: dwh
E-mail: dwh@bupt.edu.cn
Created: 2019/11/13 18:28
Description:                                              
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, BigInteger, String, UniqueConstraint, Integer, DateTime, Boolean
import datetime


Base = declarative_base()


class UserInfo(Base):
    __tablename__ = 'user_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(length=100), nullable=False)
    answer_num = Column(Integer, nullable=False)
    url = Column(String(length=128), nullable=True)
    location = Column(String(length=32))
    industry = Column(String(length=32))
    career_exp = Column(String(length=64))
    edu_exp = Column(String(length=64))
    sex = Column(Integer)

class UserInfos(Base):
    __tablename__ = 'user_infos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(length=100), nullable=False)
    answer_num = Column(Integer, nullable=False)
    ask_num = Column(Integer, nullable=True)
    location = Column(String(length=32), nullable=False)
    business = Column(String(length=32), nullable=False)
    career_exp = Column(String(length=64), nullable=False)
    position = Column(String(length=32), nullable=False)
    school = Column(String(length=64), nullable=False)
    major = Column(String(length=64), nullable=False)
    sex = Column(Integer, nullable=False)

class AnswerDetail(Base):
    __tablename__ = 'answer_detail'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    answer_title = Column(String(length=255), nullable=False)
    agree_num = Column(Integer, nullable=False)
    comment_num = Column(Integer, nullable=False)
    category = Column(String(length=255))

class AskDetail(Base):
    __tablename__ = 'ask_detail'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    ask_title = Column(String(length=255), nullable=False)
    answer_num = Column(Integer, nullable=False)
    follower_num = Column(Integer, nullable=False)
    category = Column(String(length=255))
