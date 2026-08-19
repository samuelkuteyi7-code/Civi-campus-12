import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL")

# pool_pre_ping: tests each connection with a lightweight query before
# handing it to a request. If the DB provider already closed it (common
# with hosted Postgres after idle periods), SQLAlchemy transparently
# reconnects instead of raising "SSL connection has been closed
# unexpectedly" mid-request.
#
# pool_recycle: proactively discards and replaces any connection older
# than this many seconds, so we never even try to reuse one that's likely
# gone stale. 300s (5 min) is a safe default under most providers' idle
# timeouts (which are often 5-10 min).
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
