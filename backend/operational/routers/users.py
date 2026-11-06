from fastapi import APIRouter, status, Depends, Request
from operational.database import SessionDB
from operational.models.users import UsersModel
from operational.config import MyTags
from operational.schemas.users import UserSignUpSchema, UserWithoutPasswordSchema
from fastapi.responses import JSONResponse
from operational.business_layer.users import signup_logic, login_logic, get_current_user, is_admin, is_employee, refresh_token_logic, admin_signup_logic
from fastapi.exceptions import HTTPException
from operational.custom_errors import ExistingUserByUsernameError, ExistingUserByEmailError, DatabaseError, BcryptPasswordHashingError, UserNotFoundError, IncorrectPasswordError, TokenCreationError, InvalidTokenErrorMine, RefreshTokenNotFoundError, InvalidCredentials
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from operational.config import ACCESS_TOKEN_DURATION, REFRESH_TOKEN_DURATION

router = APIRouter(prefix="/users")

'''

Here, the requests related to users and user authentication are handled. The authentication system is a JWT custom implementation using FastAPI resources.

The workflow is as follows:
Users create a user, and their hashed password is stored, no plain password is stored because that would be dangerous for the user privacy

Users send a login request with their username and password. The login function will check if the user exists, and it will hash the password given by the user and it will compare it to the stored hashed password. If the user exists and the given hashed password matches the stored hashed password, the login is successful, and two access tokens are created: a 7 days token, and a 30 min refresh token, and they are returned to the user as set cookies

When a user makes a request to a route that requires authentication, the dependency to verify user is called, and the tokens are accessed. If the refresh token gives the decoded username that matches the stored username, then the authentication is successful. If not, authentication is invalid, and frontend must make a request to the refresh token route

In the refresh token route, if the refresh token is expired but the long term token is still valid, the user will get a new refresh token. If none of them are valid, the user must log in again.

the get role function will determine if a user can or cannot access certain routes
'''


@router.post("/signup", tags=[MyTags.users])
async def signup_route(session: SessionDB, user_schema: UserSignUpSchema) -> JSONResponse: 
    '''
    This route creates a user in the database with the given user data.
    
    inputs:
        session(SessionDB): The session that is used to operate in the database
        user_schema(UserSignUpSchema): Schema containing the information of the user that will be created.

    output:
        user_response_dict(UserWithoutPasswordSchema): the user created without the password
    ''' 
    try: 
        user_schema_dict = user_schema.model_dump()

        user_response = signup_logic(session=session,
                                    username=user_schema_dict["username"],
                                    password=user_schema_dict["password"],
                                    email=user_schema_dict["email"],
                                    name=user_schema_dict["name"],
                                    lastname=user_schema_dict["lastname"]
                                    )

        user_response_dict = user_response.model_dump()

        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"user": user_response_dict})

    except ExistingUserByUsernameError as e:
        print("EXISTING USER BY USERNAME ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this username already exists")

    except ExistingUserByEmailError as e:
        print("EXISTING USER BY EMAIL ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    except BcryptPasswordHashingError as e:
        print("BCRYPT PASSWORD HASHING ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")

    except DatabaseError as e:
        print("DATABASE ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")

    except Exception as e:
        print("GENERAL EXCEPTION: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")

@router.post("/token", tags=[MyTags.users])
async def login(session: SessionDB, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> JSONResponse:
    '''
    
    This route is used to login and set the access and refresh tokens in cookies.
        
    inputs:
        session(SessionDB): The session that is used to operate in the database
        form_data(OAuth2PasswordRequestForm): form containing username and password to login
    
    output:
        response(JsonResponse): it contains the user data and two cookies: access_token and refresh token
    
    '''
    try:

        username = form_data.username
        password = form_data.password

        response_data = login_logic(session=session, username=username, password=password)

        response = JSONResponse(status_code=status.HTTP_200_OK, content={"user": response_data["user"]})

        #store access token in a cookie
        response.set_cookie(
            key="access_token",
            value=response_data["access_token"],
            httponly=False, #set to true in production
            secure=False, #set to true in production
            samesite="lax",
            max_age=ACCESS_TOKEN_DURATION*60, #it's in minutes, so convert to seconds
            path="/"
        )

        

        #store refresh token in a cookie
        response.set_cookie(
            key="refresh_token",
            value=response_data["refresh_token"],
            httponly=False, #set to true in production
            secure=False, #set to true in production
            samesite="lax",
            max_age=REFRESH_TOKEN_DURATION*24*60*60, #it's in days, so convert to minutes to seconds
            path="/"
            )

        return response

    except DatabaseError as e:
        print("DATABASE ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")

    except BcryptPasswordHashingError as e:
        print("BCRYPT PASSWORD HASHING ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")

    except UserNotFoundError as e:
        print("USER NOT FOUND ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    except IncorrectPasswordError as e:
        print("INCORRECT PASSWORD ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    except TokenCreationError as e:
        print("TOKEN CREATION ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")

    except Exception as e:
        print("GENERAL EXCEPTION: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")


@router.get("/me", tags=[MyTags.users])
async def get_me(session: SessionDB, current_user: Annotated[dict, Depends(get_current_user)], request: Request) -> JSONResponse:
    '''
    This route is used to get the profile information of the user accessing this route.

    inputs: 
        session(SessionDB): the session used to operate on the database
        current_user(UserWithoutPasswordSchema)(dependency): it is used to obtain the data of the current user if the current used is valid
        request(Request): the full request 

    output: 
        response(JsonResponse): it contains the info of the current user
    '''

    try:

        response = JSONResponse(status_code=status.HTTP_200_OK, content={"user":current_user})

        return response

    except Exception as e:
        print("GENERAL EXCEPTION: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")


@router.post("/logout", tags=[MyTags.users])
async def logout() -> JSONResponse: 
    '''
    This function is used to log out, deleting both access and refresh tokens from cookies.

    output: 
        response(JsonResponse): response containing message that the user logged out successfully
    '''
    response = JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Logged out successfully"})

    response.delete_cookie(
                           key="access_token",
                           path="/",
                           httponly=False, #true in prod
                           secure=False, #true in prod
                           samesite="lax"
                          )

    response.delete_cookie(
                           key="refresh_token",
                           path="/",
                           httponly=False, #true in prod
                           secure=False, #true in prod
                           samesite="lax"
                           )

    return response


@router.post("/refresh_token", tags=[MyTags.users])
async def refresh_token(session: SessionDB, request: Request) -> JSONResponse:
    '''
    This route is used to refresh the access token if the refresh token is still valid. 

    inputs:
        session(SessionDB): the session used to operate on the database
        request(Request): the full request 
    
    outputs:
        response(JsonResponse): response containing message that the access token was successfully refreshed 
    '''
    try:

        new_access_token = refresh_token_logic(session=session, request=request)

        response = JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Access token was successfully refreshed"})

        #store access token in a cookie
        response.set_cookie(
            key="access_token",
            value=new_access_token["new_access_token"],
            httponly=False, #set to true in production
            secure=False, #set to true in production
            samesite="lax",
            max_age=ACCESS_TOKEN_DURATION*60, #it's in minutes, so convert to seconds
            path="/"
            )

        return response

    except InvalidTokenErrorMine as e:
        print("INVALID TOKEN ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
    except RefreshTokenNotFoundError as e:
        print("REFRESH TOKEN NOT FOUND: ", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token",  headers={"WWW-Authenticate": "Bearer"})   
    
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



@router.post("/admin_signup", tags=[MyTags.admin_users])
async def admin_signup_route(session: SessionDB, user_schema: UserSignUpSchema, is_admin: Annotated[bool, Depends(is_admin)]) -> JSONResponse: 
    '''
    This route creates a user in the database with the given user data. It is used to create employee users
    
    inputs:
        session(SessionDB): The session that is used to operate in the database
        user_schema(UserSignUpSchema): Schema containing the information of the user that will be created.
        is_admin(dependency): is requires the current user to be an admin

    output:
        user_response_dict(UserWithoutPasswordSchema): the user created without the password
    ''' 
    try: 
        user_schema_dict = user_schema.model_dump()

        user_response = admin_signup_logic(session=session,
                                    username=user_schema_dict["username"],
                                    password=user_schema_dict["password"],
                                    email=user_schema_dict["email"],
                                    name=user_schema_dict["name"],
                                    lastname=user_schema_dict["lastname"]
                                    )

        user_response_dict = user_response.model_dump()

        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"user": user_response_dict})

    except ExistingUserByUsernameError as e:
        print("EXISTING USER BY USERNAME ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this username already exists")

    except ExistingUserByEmailError as e:
        print("EXISTING USER BY EMAIL ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    except BcryptPasswordHashingError as e:
        print("BCRYPT PASSWORD HASHING ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")

    except DatabaseError as e:
        print("DATABASE ERROR: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")

    except Exception as e:
        print("GENERAL EXCEPTION: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error in the server occurred")