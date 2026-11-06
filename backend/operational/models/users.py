from operational.database import Base
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, Float, ForeignKey, Numeric
from enum import Enum


'''this are the roles that users can have, customer is the default for clients, admin is the superuser with all permissions, and employee is the role for personel of the company but with limited powers. This can be later expanded and used but for now it is referencial. '''
class UserRolesModel(str, Enum):
    admin = "admin"
    employee = "employee"
    customer = "customer"

class UsersModel(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    role = Column(String(20), default=UserRolesModel.customer, nullable=False)
