"""Fix alembic_version table to match current migration files."""
import os
import sys

try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed")
    sys.exit(1)

# Use sync connection string
dsn = os.environ.get("DATABASE_URL_SYNC", "")
if not dsn:
    print("DATABASE_URL_SYNC not set")
    sys.exit(1)

# psycopg2 doesn't understand postgresql+psycopg2:// scheme
dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")

print(f"Connecting to database...")
conn = psycopg2.connect(dsn)
conn.autocommit = True
cur = conn.cursor()

# Check current version
cur.execute("SELECT version_num FROM alembic_version")
current = cur.fetchone()
print(f"Current alembic_version: {current[0] if current else 'none'}")

# Update to match the migration file
cur.execute("DELETE FROM alembic_version")
cur.execute("INSERT INTO alembic_version (version_num) VALUES (%s)", ("001_initial_schema",))
conn.commit()

print("Updated alembic_version to 001_initial_schema")

cur.close()
conn.close()