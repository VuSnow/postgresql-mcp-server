import os

# Set required env vars before any imports of ServerConfigs
os.environ.setdefault("POSTGRESQL_CONNECTION_STRING", "postgresql://test:test@localhost:5432/testdb")
