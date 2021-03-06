from sqlalchemy import Table, Column, Integer, ForeignKey, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship, class_mapper
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from sqlalchemy.exc import OperationalError, IntegrityError
import sqlalchemy


import os
import json
import datetime
import numpy as np


def attribute_names(cls):
    return [prop.key for prop in class_mapper(cls).iterate_properties
        if isinstance(prop, sqlalchemy.orm.ColumnProperty)]


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
            name = Column(String, unique=True)
            token = Column(String)

            def __str__(self):
                return f"{self.id} {self.name} {self.token}"

        self.Service = Service


        class Session_token(self.Base):
            __tablename__ = 'session_tokens'
            id = Column(Integer, primary_key=True, autoincrement=True)
            service = Column(Integer, ForeignKey(Service.id))
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
            session = Column(Integer, ForeignKey(Session_token.id))
            dataset_title = Column(String, ForeignKey(Dataset.title))
            dataset_file_id = Column(Integer, ForeignKey(Dataset.id))
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
        
            def toDict(self):
                return {k: getattr(self, k)  for k in attribute_names(self.__class__)}


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


    def insert_service(self, name, token):
        session = self.make_session()
        session.add(db.Service(
            name=name,
            token=token,
        ))
        self.commit_and_close()

    def insert_session_token(
        self, 
        service_name, 
        session_token,
    ):
        # get service id
        session = self.make_session()
        found_service = session.query(db.Service).filter(db.Service.name == service_name).first()
        if found_service is None:
            self.commit_and_close()
            raise ValueError(f"There is no service with name: {service_name}")
        
        # insert
        session.add(self.Session_token(
            service=found_service.id,
            session_token=session_token,
            issue_date=datetime.datetime.utcnow(),
            expiry_date=datetime.datetime.utcnow()+datetime.timedelta(days=1),
            active=True,
        ))
        self.commit_and_close()


    def insert_dataset_file(self, 
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

    def insert_test_row(
        self,
        service_name,
        session_token, 
        dataset_title,
        filename,
        created=None,
        retrieved=None,
        received=None,
        ai_ct=None,
        ai_left_affected_part=None,
        ai_left_affected_volume=None,
        ai_left_total_volume=None,
        ai_right_affected_part=None,
        ai_right_affected_volume=None,
        ai_right_total_volume=None,
        viewer_url=None,
        description=None,
        requests=None,
    ):
        if created is None:
            created = datetime.datetime.utcnow()

        the_service = self.get_service(service_name)
        the_session_token = self.get_session_token(session_token, the_service.id)
        if the_session_token.active == False:
            self.commit_and_close()
            raise ValueError(f"The session is inactive (session_token: {session_token})")
        the_file = self.get_file(dataset_title, filename)

        self.make_session().add(self.Test(
            session=the_session_token.id,
            dataset_title=dataset_title,
            dataset_file_id=the_file.id,
            created=created,
            retrieved=retrieved,
            ai_ct=ai_ct,
            ai_left_affected_part=ai_left_affected_part,
            ai_left_affected_volume=ai_left_affected_volume,
            ai_left_total_volume=ai_left_total_volume,
            ai_right_affected_part=ai_right_affected_part,
            ai_right_affected_volume=ai_right_affected_volume,
            ai_right_total_volume=ai_right_total_volume,
            viewer_url=viewer_url,
            description=description,
            requests=requests
        ))
        self.commit_and_close()

    def get_service(
        self, 
        service_name
    ):
        session = self.make_session()
        the_service = session.query(self.Service).filter(self.Service.name==service_name).one_or_none()
        if the_service is None:
            self.commit_and_close()
            raise ValueError(f"Therer is no such a service: {service_name}")
        return the_service

    def get_session_token(
        self,
        session_token,
        service_id,
    ):
        session = self.make_session()
        the_session = session.query(self.Session_token) \
                             .filter(self.Session_token.session_token==session_token) \
                             .filter(self.Session_token.service == service_id) \
                             .one_or_none()
        if the_session is None:
            self.commit_and_close()
            raise ValueError(f"There is no such a session (session_token: {session_token})")
        return the_session
            
    def get_file(
        self, 
        dataset_title,
        filename,
    ):
        session = self.make_session()
        the_file = session.query(self.Dataset).filter(self.Dataset.title==dataset_title) \
                                              .filter(self.Dataset.filename==filename)   \
                                              .one_or_none()
        if the_file is None:
            self.commit_and_close()
            raise ValueError(f"There is no such a file in datasets (title: {dataset_title}, filename: {filename})")
        return the_file

    def get_test_row(
        self, 
        service_name,
        session_token, 
        dataset_title,
        filename,
    ):
        the_service = self.get_service(service_name)
        the_session_token = self.get_session_token(session_token, the_service.id)
        if the_session_token.active == False:
            self.commit_and_close()
            raise ValueError(f"The session is inactive (session_token: {session_token})")
        the_file = self.get_file(dataset_title, filename)

        the_test_row = self.make_session().query(self.Test).filter(self.Test.session==the_session_token.id) \
                                               .filter(self.Test.dataset_title==dataset_title)  \
                                               .filter(self.Test.dataset_file_id==the_file.id)  \
                                               .one_or_none()
        if the_test_row is None:
            self.commit_and_close()
            raise ValueError(f"There is no such a test row.")
        return the_test_row


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

    db.insert_service(test_name, test_token)

    session = db.make_session()
    services = session.query(db.Service).filter(db.Service.name == test_name).all()
    assert len(services) == 1
    assert services[0].token == test_token


def test_dataset_row_insert(db):
    test_title = 'test_title'
    test_filename = 'test_filename'

    db.insert_dataset_file(test_title, test_filename)

    session = db.make_session()
    datatasets = session.query(db.Dataset).filter(db.Dataset.title == test_title).all()
    assert len(datatasets) == 1
    assert datatasets[0].filename == test_filename


def test_session_token_insert(db):
    # insert 
    service_name = 'test_service2'
    service_token = 'service_token'
    session_token = 'session_token'
    db.insert_service(service_name, service_token)
    db.insert_session_token(service_name, session_token)

    # check
    session = db.make_session()
    service = session.query(db.Service).filter(db.Service.name == service_name).one_or_none()
    the_token = session.query(db.Session_token).filter(db.Session_token.service == service.id).one_or_none()
    assert the_token.session_token == session_token


def test_test_row_insert(db):
    service_name = 'test_service3'
    service_token = 'service_token'
    session_token = 'session_token'
    dataset_title = 'test_dataset_title'
    filename = 'test_filename'
    ai_ct = 5
    db.insert_dataset_file(
        dataset_title, 
        filename
    )
    db.insert_service(
        service_name, 
        service_token
    )
    db.insert_session_token(
        service_name, 
        session_token
    )
    db.insert_test_row(
        service_name, 
        session_token,
        dataset_title,
        filename,
        ai_ct=ai_ct,
    )

    test_row = db.get_test_row(
        service_name,
        session_token, 
        dataset_title,
        filename
    )
    assert test_row.ai_ct == ai_ct


if __name__ == "__main__":
    try:
        os.remove(db_path)
    except:
        pass

    db_path = os.path.join(os.getcwd(), 'test_db.sqlite')
    db = dbManager(db_path)

    test_service_insert(db)
    db.empty()

    test_dataset_row_insert(db)
    db.empty()

    test_session_token_insert(db)
    db.empty()
    
    test_test_row_insert(db)
    db.empty()

    os.remove(db_path)
