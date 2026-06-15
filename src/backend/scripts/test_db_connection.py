#!/usr/bin/env python3
"""Prueba simple de conexión a la base de datos usando Settings.

Ejecuta desde la raíz del repo:
  cd src/backend
  python scripts/test_db_connection.py

Usará `database_url_sync` definido en `.env` o en los defaults de `Settings`.
"""
from __future__ import annotations

from sqlalchemy import create_engine, text

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    url = settings.database_url_sync
    print("Usando URL (sync):", url)

    engine = create_engine(url)
    with engine.connect() as conn:
        try:
            r = conn.execute(text("SELECT * FROM products WHERE id = 9410"))
            print("Product ->", r.fetchone())

            r = conn.execute(text("SELECT version()"))
            print("Postgres version:", r.scalar())
        except Exception as exc:
            print("Error conectando a la base:", exc)


if __name__ == "__main__":
    main()
