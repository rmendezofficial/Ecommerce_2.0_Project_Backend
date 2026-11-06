from operational.database import get_db
from operational.models.users import UsersModel
from operational.business_layer.users import hash_password

'''
file to generate the first admin. It is intended to be used once during development, so it is less informal. Probably delete this file altogether later 

SECRET KEY: v_JagayXc7QSxhNirCoO9ZgbzaMIK9xD75tbEr5nFaI
'''



def generate_first_admin(username: str, password: str, email:str, name: str, lastname: str, secret_key: str):

    db_generator = get_db()
    db = next(db_generator)

    if secret_key == "v_JagayXc7QSxhNirCoO9ZgbzaMIK9xD75tbEr5nFaI":

        hashed_password = hash_password(password=password)

        admin_user = UsersModel(username=username, hashed_password=hashed_password, email=email, name=name, lastname=lastname, role="admin")

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("admin user created successfully")

    else: 
        print("ERROR")


generate_first_admin("user_admin", "111ricardo mendez", "ricgabadmin@gmail.com", "Admin name", "Admin lastname", "v_JagayXc7QSxhNirCoO9ZgbzaMIK9xD75tbEr5nFaI")