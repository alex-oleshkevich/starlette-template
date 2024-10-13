from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.config import settings

TEST_DATABASE_URL = settings.database_url
TEST_SYNC_DATABASE_URL = TEST_DATABASE_URL.replace("+psycopg_async", "+psycopg")

test_db_engine = create_engine(TEST_SYNC_DATABASE_URL)
Session = scoped_session(sessionmaker(test_db_engine))
