import os
import tempfile

_db = tempfile.NamedTemporaryFile(prefix="ids-test-", suffix=".db", delete=False)
_db.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _db.name.replace("\\", "/")
os.environ["MODEL_PATH"] = "models/test-missing-model.pkl"


def pytest_sessionfinish(session, exitstatus) -> None:
    from src.api.database import engine

    engine.dispose()
    try:
        os.remove(_db.name)
    except OSError:
        pass
