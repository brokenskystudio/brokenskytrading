import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.security import Security


CATALOG_PATH = Path(__file__).parents[1] / "data" / "securities.csv"


def seed_security_catalog(db: Session) -> None:
    with CATALOG_PATH.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    existing_identities = set(
        db.execute(select(Security.symbol, Security.exchange)).all()
    )

    for row in rows:
        identity = (row["symbol"], row["exchange"])
        if identity in existing_identities:
            continue
        row["is_active"] = row["is_active"].lower() == "true"
        db.add(Security(**row))
    db.commit()
