from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import yaml
from pydantic import BaseModel


def parse_db_parameters():
    with open('dbconfig.yml', 'r') as file:
        parameters = yaml.safe_load(file)
    return DbConnection.model_validate(parameters)


class DbParameters(BaseModel):
    """Parameters for db connection"""
    username: str
    password: str
    url: str
    port: int
    db_name: str


class DbConnection(BaseModel):
    db_parameters: DbParameters


def get_url_database():
    dbConnection = parse_db_parameters()
    return (
        f'postgresql://{dbConnection.db_parameters.username}'
        f':{dbConnection.db_parameters.password}@{dbConnection.db_parameters.url}'
        f':{dbConnection.db_parameters.port}/{dbConnection.db_parameters.db_name}'
    )

URL_DATABASE = get_url_database()


engine = create_engine(URL_DATABASE)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
Base = declarative_base()
