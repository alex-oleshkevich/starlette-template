from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.config import settings

TEST_DATABASE_URL = settings.database_url
TEST_SYNC_DATABASE_URL = TEST_DATABASE_URL.replace("+psycopg_async", "+psycopg")
assert "_test" in TEST_DATABASE_URL, "Database URL must contain '_test' to prevent data loss"

test_db_engine = create_engine(TEST_SYNC_DATABASE_URL)
SyncSession: scoped_session[Session] = scoped_session(sessionmaker(test_db_engine))
