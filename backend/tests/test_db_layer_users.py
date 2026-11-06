from operational.db_layer.users import get_user_by_username_db, add_user_db
from operational.database import get_db
from operational.custom_errors import DatabaseError
import pytest


'''


#used to handle the session
@pytest.fixture
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

#========================================================================
#get_user_by_username_db()

def test_get_user_by_username_db_found(session):

    user_db = get_user_by_username_db(session=session, username="mock user 1234")

    assert user_db.username == "mock user 1234"

def test_get_user_by_username_db_not_found(session):

    user_db = get_user_by_username_db(session=session, username="FalseUser")
    
    assert user_db is None

def test_get_user_by_username_db_type_error(session):

    with pytest.raises(TypeError):
        get_user_by_username_db(session=session, username=212)

#========================================================================
#add_user_db()

def test_add_user_db_success(session):

    mock_user={
        "username": "mock user 1234",
        "hashed_password": "hashed false password",
        "email": "mockemail@gmail.com", 
        "name": "mock name",
        "lastname": "mock lastname",
    }

    user = add_user_db(session=session, 
                       username=mock_user["username"], hashed_password=mock_user["hashed_password"], email=mock_user["email"],
                       name=mock_user["name"], 
                       lastname=mock_user["lastname"])


    assert user.username == mock_user["username"]
    assert user.hashed_password == mock_user["hashed_password"]
    assert user.email == mock_user["email"]
    assert user.name == mock_user["name"]
    assert user.lastname == mock_user["lastname"]

def test_add_user_db_db_error(session):

    mock_user={
        "username": 12345,
        "hashed_password": "hashed false password",
        "email": "mockemail@gmail.com", 
        "name": "mock name",
        "lastname": "mock lastname",
    }

    with pytest.raises(DatabaseError):
        add_user_db(session=session, 
                       username=mock_user["username"], hashed_password=mock_user["hashed_password"], email=mock_user["email"],
                       name=mock_user["name"], 
                       lastname=mock_user["lastname"])
        
'''