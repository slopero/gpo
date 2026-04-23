from db.connection import Base, engine
from db import params_model 

def create_db():
    Base.metadata.create_all(bind=engine)
