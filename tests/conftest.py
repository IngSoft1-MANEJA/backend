import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Base


@pytest.fixture()
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)

    # Create a Session
    session = Session()

    yield session  # Provide the fixture value

    # Close the session
    session.close()
    Base.metadata.drop_all(engine)  # Drop tables
