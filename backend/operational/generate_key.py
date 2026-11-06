import secrets

'''
This file is ran to generate a secret key for access and refresh tokens
'''
print("GENERATING KEY")
secret_key = secrets.token_urlsafe(32)
print(secret_key)