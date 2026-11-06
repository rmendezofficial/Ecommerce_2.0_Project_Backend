from fastapi import FastAPI
from contextlib import asynccontextmanager
from operational.database import Base, engine
from operational.routers import users, products

@asynccontextmanager 
async def lifespan(app: FastAPI): #Right now I only use it to create the tables if they do not exist, but later it will be used for other things
    
    Base.metadata.create_all(bind=engine)

    yield

#create app
app = FastAPI(lifespan=lifespan)

#include routers
app.include_router(users.router)
app.include_router(products.router)
