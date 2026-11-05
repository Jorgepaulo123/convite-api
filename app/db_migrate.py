from sqlalchemy import inspect, text

from app.database import engine


def ensure_guest_checkin_column() -> None:
    """Adiciona checked_in_at em bases já existentes (Postgres/SQLite)."""
    insp = inspect(engine)
    if "guests" not insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("guests")}
    if "checked_in_at" in cols:
        return
    dialect = engine.dialect.name
    if dialect == "sqlite":
        ddl = "ALTER TABLE guests ADD COLUMN checked_in_at DATETIME"
    else:
        ddl = "ALTER TABLE guests ADD COLUMN checked_in_at TIMESTAMPTZ"
    with engine.begin() as conn:
        conn.execute(text(ddl))
