from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event


# SQLALCHEMY_DATABASE_URL = "sqlite:///./maindb.db"
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/maindb.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)


def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute("pragma foreign_keys=ON")


event.listen(engine, "connect", _fk_pragma_on_connect)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def get_db_factory():
#     """Returns a function that creates new database sessions"""
#     # This should be similar to your get_db function but returns the function
#     # that creates sessions rather than a session directly
    
#     def _get_db():
#         db = SessionLocal()
#         try:
#             return db
#         except Exception:
#             db.close()
#             raise
            
#     return _get_db

# def get_db():
#     """Returns a new database session"""
    
#     db = SessionLocal()
#     try:
#         return db
#     except Exception:
#         db.close()
#         raise