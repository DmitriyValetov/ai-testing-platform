from sqlalchemy import Table, Column, Integer, ForeignKey, String, Float, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from sqlalchemy.exc import OperationalError, IntegrityError

import os
import json
import datetime
import numpy as np


class dbManager:

    def __init__(self, db_abs_path):
        self.db_path = db_abs_path
        self.Base = declarative_base()

        class Dataset(self.Base):
            __tablename__ = 'datasets'
            id = Column(Integer, primary_key=True, autoincrement=True)
            title = Column(String)
            filename = Column(String)
            var1 = Column(String)
            var2 = Column(String)
            var3 = Column(String)
            var4 = Column(String)
            var5 = Column(String)
            added = Column(DateTime, default=datetime.datetime.utcnow)

            def __str__(self):
                return f"{self.id} {self.title} {self.filename}"

        self.Dataset = Dataset


        class Service(self.Base):
            __tablename__ = 'services'
            id = Column(Integer, primary_key=True, autoincrement=True)
            name = Column(String)
            token = Column(String)

            def __str__(self):
                return f"{self.id} {self.name} {self.token}"

        self.Service = Service


        class Session_token(self.Base):
            __tablename__ = 'session_tokens'
            id = Column(Integer, primary_key=True, autoincrement=True)
            service = Column(Integer)
            session_token = Column(String)
            issue_date = Column(DateTime)
            expiry_date = Column(DateTime)
            active = Column(Boolean)

            def __str__(self):
                return f"{self.id} {self.service} {self.session_token} {self.issue_date} {self.expiry_date} {self.active}"

        self.Session_token = Session_token


        class Test(self.Base):
            __tablename__ = 'testing'
            id = Column(Integer, primary_key=True, autoincrement=True)
            session = Column(Integer)
            dataset_title = Column(String)
            dataset_file_id = Column(Integer)
            created = Column(DateTime, default=datetime.datetime.utcnow)
            retrieved = Column(DateTime)
            received = Column(DateTime)
            ai_ct = Column(Integer)
            ai_left_affected_part = Column(Float)
            ai_left_affected_volume = Column(Float)
            ai_left_total_volume = Column(Float)
            ai_right_affected_part = Column(Float)
            ai_right_affected_volume = Column(Float)
            ai_right_total_volume = Column(Float)
            viewer_url = Column(String)
            description = Column(String)
            requests = Column(String)

            def __str__(self):
                return f"{self.id} {self.session} {self.dataset_title} {self.dataset_file_id} {self.created} {self.retrieved} {self.received}"
        
        self.Test = Test


        # all classes declarated, now init part of dbManager
        engine = self.make_engine()
        self.Base.metadata.create_all(engine)



    def make_engine(self, echo=False):
        engine = create_engine('sqlite:///{}'.format(self.db_path), echo=echo)
        return engine
    

    def commit_and_close(self):
        self.session.commit()

        try:
            self.session.close()
        except:
            pass

        try:
            self.engine.dispose()
        except:
            pass


    def make_session(self):
        self.engine = self.make_engine()
        self.session = sessionmaker(bind=self.engine)()
        return self.session


    def add_service(self, name, token):
        session = self.make_session()
        session.add(db.Service(
            name=name,
            token=token,
        ))
        self.commit_and_close()


    def add_dataset_row(self, 
        title,
        filename,
        var1=None,
        var2=None,
        var3=None,
        var4=None,
        var5=None
    ):
        session = self.make_session()
        session.add(db.Dataset(
            title=title,
            filename=filename,
            var1=var1,
            var2=var2,
            var3=var3,
            var4=var4,
            var5=var5,
        ))
        self.commit_and_close()

    def empty(self):
        session = self.make_session()
        session.query(self.Service).delete()
        session.query(self.Dataset).delete()
        session.query(self.Session_token).delete()
        session.query(self.Test).delete()
        self.commit_and_close()



def test_service_insert(db):
    test_name = 'test_service'
    test_token = '123qwerty654'

    db.add_service(test_name, test_token)

    session = db.make_session()
    services = session.query(db.Service).filter(db.Service.name == test_name).all()
    assert len(services) == 1
    assert services[0].token == test_token


def test_dataset_row_insert(db):
    test_title = 'test_title'
    test_filename = 'test_filename'

    db.add_dataset_row(test_title, test_filename)

    session = db.make_session()
    datatasets = session.query(db.Dataset).filter(db.Dataset.title == test_title).all()
    assert len(datatasets) == 1
    assert datatasets[0].filename == test_filename

    

if __name__ == "__main__":
    db_path = os.path.join(os.getcwd(), 'test_db.sqlite')
    db = dbManager(db_path)
    db.empty()

    test_service_insert(db)
    test_dataset_row_insert(db)

    os.remove(db_path)
    