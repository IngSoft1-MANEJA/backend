from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_FILENAME


# Configuración de la base de datos
engine = create_engine(f'sqlite:///{DATABASE_FILENAME}', echo=True)
Base = declarative_base()

# Crea una sesión
Init_Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
run_session = Init_Session()

def init_db():
    import app.models
    Base.metadata.create_all(bind=engine)
    print("Database initialized")