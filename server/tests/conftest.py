import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Create tables synchronously before any tests run to avoid asyncio loop conflicts.
# This runs once at pytest collection time, before any fixtures or tests.
from sqlalchemy import create_engine
from server.config import settings
from server.db import Base

# Use sync engine for table creation (independent of test event loops)
sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(sync_url, echo=False)
# Drop and recreate for clean state each test run
Base.metadata.drop_all(sync_engine)
Base.metadata.create_all(sync_engine, checkfirst=True)
sync_engine.dispose()
