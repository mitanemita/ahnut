import asyncio
import os
import tempfile

_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_db}"
os.environ["YOOKASSA_CHECK_IP"] = "false"
os.environ["INTERNAL_TOKEN"] = "test-internal"
os.environ["N8N_GENERATE_URL"] = ""
os.environ["FILES_DIR"] = tempfile.mkdtemp()

import pytest  # noqa: E402

from app.db import engine  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    async def reset():
        async with engine.begin() as c:
            await c.run_sync(Base.metadata.drop_all)
            await c.run_sync(Base.metadata.create_all)
    asyncio.run(reset())
    yield
