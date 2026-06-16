import os
import sys
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"

# Patch init_db to be a no-op for tests (no real PostgreSQL needed)
import server.db
server.db.init_db = AsyncMock(return_value=None)
