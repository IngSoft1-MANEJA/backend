from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_FILENAME

# Configuración de la base de datos
engine = create_engine(f'sqlite:///{DATABASE_FILENAME}', echo=True)
Base = declarative_base()

# Crea una sesión
Init_Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
run_session = Init_Session()

def init_db():
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("Database initialized")

def delete_db():
    Base.metadata.drop_all(bind=engine)
    print("Database deleted")