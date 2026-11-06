

class DatabaseError(Exception):
    pass

class ExistingUserByUsernameError(Exception):
    pass

class ExistingUserByEmailError(Exception):
    pass

class BcryptPasswordHashingError(Exception):
    pass

class UserNotFoundError(Exception):
    pass

class IncorrectPasswordError(Exception):
    pass


class TokenCreationError(Exception):
    pass

class AccessTokenNotFound(Exception):
    pass

class InvalidCredentials(Exception):
    pass

class RefreshTokenNotFoundError(Exception):
    pass

class InvalidTokenErrorMine(Exception):
    pass