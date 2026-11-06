from operational.database import SessionDB
from operational.models.users import UsersModel
from operational.custom_errors import DatabaseError
from typing import Any
from sqlalchemy.exc import SQLAlchemyError

def get_user_by_username_db(session: SessionDB, username: str) -> UsersModel | None:
    '''
    Get existing user from database by username
    
    inputs:
        session(SessionDB): the session to operate on the database
        username(str): the username used to find existing user

    output:
        user_db(Users): the user object model
    '''

    try:

        user_db = session.query(UsersModel).filter(UsersModel.username==username).first()

        return user_db

    except SQLAlchemyError as sqlalchemy_e:
        raise DatabaseError("Error occurred when getting user from database by username") from sqlalchemy_e

    except Exception as e: 
        raise 

def get_user_by_email_db(session: SessionDB, email: str) -> UsersModel | None : 
    '''
    Get existing user from database by email

    inputs:
        session(SessionDB): the session to operate on the database
        email(str): the email used to find existing user

    output:
        user_db(Users): the user object model found; if not found, return None
    '''

    try:

        user_db = session.query(UsersModel).filter(UsersModel.email==email).first()

        return user_db

    except SQLAlchemyError as sqlalchemy_e:
        raise DatabaseError("An error occurred when getting user from database by email") from sqlalchemy_e

    except Exception as e:
        raise
        

def add_user_db(session: SessionDB, username: str, hashed_password: str, email: str, name: str, lastname: str) -> UsersModel: 
    '''
    Create a user in the database in the users table. 

    inputs:
        session(SessionDB): the session to operate on the database
        username(str): the username of the new user
        hashed_password(str): the hashed password of the new user
        email(str): the email of the new user
        name(str): the name of the new user
        lastname(str): the lastname of the user

    output:
        user(Users): the user object model created
    '''

    try:

        user = UsersModel(username=username, hashed_password=hashed_password, email=email, name=name, lastname=lastname)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    except SQLAlchemyError as sqlalchemy_e:
        session.rollback()
        raise DatabaseError("An error occurred when adding the user to the database") from sqlalchemy_e
    except Exception as e:
        raise



def admin_add_user_db(session: SessionDB, username: str, hashed_password: str, email: str, name: str, lastname: str) -> UsersModel: 
    '''
    Create a user in the database in the users table. It requires admin credentials and it is used to create employee accounts. 

    inputs:
        session(SessionDB): the session to operate on the database
        username(str): the username of the new user
        hashed_password(str): the hashed password of the new user
        email(str): the email of the new user
        name(str): the name of the new user
        lastname(str): the lastname of the user

    output:
        user(Users): the user object model created
    '''

    try:

        user = UsersModel(username=username, hashed_password=hashed_password, email=email, name=name, lastname=lastname, role="employee")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    except SQLAlchemyError as sqlalchemy_e:
        session.rollback()
        raise DatabaseError("An error occurred when adding the user to the database") from sqlalchemy_e
    except Exception as e:
        raise

