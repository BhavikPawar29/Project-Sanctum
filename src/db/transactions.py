from contextlib import contextmanager

@contextmanager
def transactional(db):
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise
