from operational.db_layer.users import get_user_by_username_db, get_user_by_email_db, add_user_db, admin_add_user_db
from operational.database import SessionDB
from typing import Any, Annotated
from operational.custom_errors import ExistingUserByUsernameError, ExistingUserByEmailError, BcryptPasswordHashingError, DatabaseError, UserNotFoundError, IncorrectPasswordError, TokenCreationError, AccessTokenNotFound, InvalidCredentials, RefreshTokenNotFoundError, InvalidTokenErrorMine
from passlib.context import CryptContext
from operational.schemas.users import UserWithoutPasswordSchema
from operational.models.users import UsersModel
from datetime import timedelta, datetime, timezone
from operational.config import ACCESS_TOKEN_DURATION, REFRESH_TOKEN_DURATION, SECRET_KEY, ALGORITHM, MyRoles
import jwt
from fastapi import Request, status, Depends
from fastapi.exceptions import HTTPException


#context used to hash passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

access_token_expires = timedelta(minutes=ACCESS_TOKEN_DURATION)
refresh_token_expires = timedelta(days=REFRESH_TOKEN_DURATION)

def hash_password(password: str) -> str:
    '''
    this function hashes the plain password and returns it. 
    
    inputs: 
        password(str): the plain text password

    output:
        hashed_password(str): the hashed password to be used in database 
    '''
    try:

        hashed_password = pwd_context.hash(password)

        return hashed_password

    except Exception as e:
        raise BcryptPasswordHashingError("An error occurred when hashing the password") from e

def verify_password(password: str, hashed_password: str) -> bool:
    '''
    This function verifies that the password and the hashed_password match.

    inputs: 
        password(str): the password given by the user in the request used to try to login
        hashed_password(str): the hashed password of the user stored in the database 

    output: 
        verification(boolean): True if the passwords match, False if they do not match. 
    '''
    try:
    
        verification = pwd_context.verify(password, hashed_password)
    
        return verification
    
    except Exception as e:
        raise BcryptPasswordHashingError("An error occurred when verifying the password") from e


def create_token(data: dict, expires_delta: timedelta) -> Any:
    '''
    This function is used to create the tokens.

    inputs:
        data(dict): the final encoded object is a dict that contains "sub" (the value) and "exp" (expiration), as follows: {"sub":username, "exp":time_of_expiration}; however, as input it only contains "sub"
        expires_delta(timedelta): the duration or lifespan of the token

    output:
        encoded_jwt(str): the encoded token
        
    '''
    try:
        #copy the data to encode
        data_to_encode = data.copy()

        #create the expiration date: current time+lifespan of the token
        expire=datetime.now(timezone.utc)+expires_delta

        #add the "exp" key to the dict data_to_encode
        data_to_encode.update({"exp":expire})

        #encode the token
        encoded_jwt = jwt.encode(data_to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt

    except Exception as e:
        raise TokenCreationError("An error occurred when creating the token") from e
    
    


def user_model_to_schema(user_model: UsersModel) -> UserWithoutPasswordSchema:
    '''
    This function receives a user model, extracts its data, and returns a user schema. WITHOUT THE PASSWORD.

    inputs: 
        user_model(UsersModel): the user model

    output:
        user_schema(UserWithoutPasswordSchema): the user schema
    '''

    user_schema = UserWithoutPasswordSchema(username=user_model.username,
     email=user_model.email, 
     name=user_model.name, 
     lastname=user_model.lastname, 
     role=user_model.role
    )

    return user_schema
    

def signup_logic(session: SessionDB, username: str, password: str, email: str, name: str, lastname: str) -> UserWithoutPasswordSchema: 
    '''
    This function checks that an existing user with the given username or email doesn't exist, and creates a user in the database.

    inputs: 
        session(SessionDB): the session used to operate on the database
        username(str): the username for the new user
        password(str): the plain password for the new user
        email(str): the email for the new user
        name(str): the name for the new user
        lastname(str): the lastname for the new user

    output:
        user_dict(dict): a dictionary representing the user created, without returning the password
    '''

    try:

        #convert username and email to lowercase to enforce that they are lowercase in the database; the other fields won't be enforced to be lowercase
        username_lower = username.lower()
        email_lower = email.lower()

        #check existing user by username
        existing_user_by_username = get_user_by_username_db(session=session, username=username_lower)

        if existing_user_by_username:
            raise ExistingUserByUsernameError("A user with this username already exists")

        #check existing user by email
        existing_user_by_email = get_user_by_email_db(session=session, email=email_lower)

        if existing_user_by_email: 
            raise ExistingUserByEmailError("A user with this email already exists")

        #hash password
        hashed_password = hash_password(password)

        #add user to database

        user_created_model = add_user_db(session=session,
                                         username=username_lower, 
                                         hashed_password=hashed_password,
                                         email=email_lower,
                                         name=name,
                                         lastname=lastname
                                        )

        user_without_password = user_model_to_schema(user_model=user_created_model)

        return user_without_password

    except BcryptPasswordHashingError:
        raise

    except DatabaseError:
        raise

    except Exception as e:
        raise


def login_logic(session: SessionDB, username: str, password:str) -> dict:
    '''
    This function authenticates the user. It checks that the username and the password are correct, and creates the access and refresh tokens.

    inputs: 
        session(SessionDB): the session used to operate on the database
        username(str): the username given by the user in the request
        password(str): the password given by the user in the request

    output: 
        response(dict): dict that contains the user without password (UserWithoutPasswordSchema), the access token(str), and the refresh token(str)
    '''
    try:

        username_lower = username.lower()

        #check that the user with this username exists
        existing_user_by_username = get_user_by_username_db(session=session, username=username_lower)

        if not existing_user_by_username:
            raise UserNotFoundError("User with this username was not found")

        verified = verify_password(password=password, hashed_password=existing_user_by_username.hashed_password)

        if not verified:
            raise IncorrectPasswordError("Incorrect password")

        #user to return
        user_without_password = user_model_to_schema(existing_user_by_username)

        #convert from schema to dict
        user_without_password_dict = user_without_password.model_dump()

        #create access and refresh tokens
        data_to_encode = {"sub": existing_user_by_username.username}

        access_token = create_token(data=data_to_encode, expires_delta=access_token_expires)

        refresh_token = create_token(data=data_to_encode, expires_delta=refresh_token_expires)

        response = {"user": user_without_password_dict, "access_token": access_token, "refresh_token": refresh_token}

        return response

    except Exception:
        raise 


def get_current_user(session: SessionDB, request: Request) -> dict:
    '''
    This function validates the current user and returns it.

    inputs:
        session(SessionDB): the session used to operate on the database
        request(Request): the full request 

    output:
        user_response_dict(dict): the current user schema
    '''
    try:

        access_token = request.cookies.get("access_token")

        if not access_token:
            raise AccessTokenNotFound("Access token not found")

        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])

        username_decoded = payload.get('sub')

        if username_decoded is None:
            raise InvalidCredentials("Could not validate credentials")

        current_user = get_user_by_username_db(session=session, username=username_decoded)

        if not current_user:
            raise UserNotFoundError("User with this username was not found")

        user_response = user_model_to_schema(current_user)

        user_response_dict = user_response.model_dump()

        return user_response_dict
        

    except jwt.InvalidTokenError as e:
        print("INVALID TOKEN ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    except AccessTokenNotFound as e:
        print("ACCESS TOKEN NOT FOUND: ", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token",  headers={"WWW-Authenticate": "Bearer"})   

    except InvalidCredentials as e:
        print("INVALID CREDENTIALS: ", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

    except UserNotFoundError as e:
        print("USER NOT FOUND ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

    except DatabaseError as e:
        print("DATABASE ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")

    except Exception as e:
        print("GENERAL EXCEPTION: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")

def refresh_token_logic(session: SessionDB, request: Request) -> bool : 
    '''
    This function is used to refresh the access token if the refresh token is still valid.
    
    inputs:
        session(SessionDB): the session used to operate on the database
        request(Request): the full request 

    outputs:
        dict(dict): dict containing the new access token
        
    '''
    try:

        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            raise RefreshTokenNotFoundError("Refresh token not found")

        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])    

        username_decoded = payload.get('sub')
        
        if username_decoded is None:
            raise InvalidCredentials("Could not validate credentials")
        
        current_user = get_user_by_username_db(session=session, username=username_decoded)
        
        if not current_user:
            raise UserNotFoundError("User with this username was not found")
        
        #create new access token
        data_to_encode = {"sub": current_user.username}
        
        access_token = create_token(data=data_to_encode, expires_delta=access_token_expires)

        return {"new_access_token": access_token}
        

    except jwt.InvalidTokenError as e:
            print("INVALID TOKEN ERROR: ", e)
            raise InvalidTokenErrorMine("Invalid or expired token")

def is_admin(current_user: Annotated[dict, Depends(get_current_user)]):
    '''
    This function is used to validate admin credentials. 
    
    inputs:
        current_user(UserWithoutPasswordSchema)(dependency): it is used to obtain the data of the current user if the current used is valid
        
    output:
        True(bool): true if the client is admin, exception raised if the client is not admin
    '''
    try:

        if current_user["role"] != MyRoles.admin:
            raise InvalidCredentials("Could not validate credentials")

        return True

    except InvalidCredentials as e:
        print("INVALID CREDENTIALS (ADMIN): ", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

def is_employee(current_user: Annotated[dict, Depends(get_current_user)]):
    '''
        This function is used to validate employee credentials. Admins also have the powers of employees, but employees don't have the power of admins. 
        
        inputs:
            current_user(UserWithoutPasswordSchema)(dependency): it is used to obtain the data of the current user if the current used is valid
            
        output:
            True(bool): true if the client is employee, exception raised if the client is not employee
        '''
    try:

        if current_user["role"] == MyRoles.customer:
            raise InvalidCredentials("Could not validate credentials")

        return True

    except InvalidCredentials as e:
        print("INVALID CREDENTIALS (EMPLOYEE): ", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

def admin_signup_logic(session: SessionDB, username: str, password: str, email: str, name: str, lastname: str) -> UserWithoutPasswordSchema: 
    '''
    This function checks that an existing user with the given username or email doesn't exist, and creates a user in the database. It requires admin credentials to use, and it is used to create employee accounts. 

    inputs: 
        session(SessionDB): the session used to operate on the database
        username(str): the username for the new user
        password(str): the plain password for the new user
        email(str): the email for the new user
        name(str): the name for the new user
        lastname(str): the lastname for the new user

    output:
        user_dict(dict): a dictionary representing the user created, without returning the password
    '''

    try:

        #convert username and email to lowercase to enforce that they are lowercase in the database; the other fields won't be enforced to be lowercase
        username_lower = username.lower()
        email_lower = email.lower()

        #check existing user by username
        existing_user_by_username = get_user_by_username_db(session=session, username=username_lower)

        if existing_user_by_username:
            raise ExistingUserByUsernameError("A user with this username already exists")

        #check existing user by email
        existing_user_by_email = get_user_by_email_db(session=session, email=email_lower)

        if existing_user_by_email: 
            raise ExistingUserByEmailError("A user with this email already exists")

        #hash password
        hashed_password = hash_password(password)

        #add user to database

        user_created_model = admin_add_user_db(session=session,
                                         username=username_lower, 
                                         hashed_password=hashed_password,
                                         email=email_lower,
                                         name=name,
                                         lastname=lastname
                                        )

        user_without_password = user_model_to_schema(user_model=user_created_model)

        return user_without_password

    except BcryptPasswordHashingError:
        raise

    except DatabaseError:
        raise

    except Exception as e:
        raise