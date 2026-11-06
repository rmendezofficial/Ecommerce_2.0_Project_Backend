from enum import Enum


'''

HERE ARE STORED THE SECRET KEYS OF THE SERVER

They are strings because I am in development, but once the server is deployed they will be server environment variables

'''

#In production, it will be os.getenv(URLKEY) as a secret env key of server
DATABASE_URL = "url to connect to the database" 

#tags to use in fastapi docs
class MyTags(str, Enum):
    users = "users"
    admin_users = "admin_users"
    admin_products = "admin_products"

class MyRoles(str, Enum):
    customer = "customer"
    employee = "employee"
    admin = "admin"

#Duration of access tokens, in minutes
ACCESS_TOKEN_DURATION = 30

#Duration of refresh tokens, in days
REFRESH_TOKEN_DURATION = 7

#secret key used for encryptation
SECRET_KEY = "xZ3EyF9_okxbC8f-E-spLLlZGIzz0avNzuFEcAG6e5M"

#algorithm used to encrypt and decode tokens
ALGORITHM="HS256"