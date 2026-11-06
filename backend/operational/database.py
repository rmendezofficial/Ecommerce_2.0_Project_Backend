from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Annotated
from operational.config import DATABASE_URL

#create engine to connect to database 
engine = create_engine(DATABASE_URL)

#create session
SessionLocal = sessionmaker(
    bind = engine, 
    autocommit = False, 
    autoflush = False
)

#this will be innherited by models to create tables
class Base(DeclarativeBase):
    pass

#this will be used as a dependency to operate on the database
def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

#dependency that will be used to operate on the database, it is passed to routes
SessionDB=Annotated[Session, Depends(get_db)]

