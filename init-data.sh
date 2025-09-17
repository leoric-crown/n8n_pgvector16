#!/bin/bash
set -e;


if [ -n "${POSTGRES_NON_ROOT_USER:-}" ] && [ -n "${POSTGRES_NON_ROOT_PASSWORD:-}" ]; then
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
		DO \$\$
		BEGIN
			IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_NON_ROOT_USER}') THEN
				CREATE USER ${POSTGRES_NON_ROOT_USER} WITH PASSWORD '${POSTGRES_NON_ROOT_PASSWORD}';
			END IF;
		END
		\$\$;
		GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_NON_ROOT_USER};
		GRANT CREATE ON SCHEMA public TO ${POSTGRES_NON_ROOT_USER};
		CREATE EXTENSION IF NOT EXISTS vector;
	EOSQL
else
    echo "SETUP INFO: No Environment variables given!"
fi

# Langfuse database setup (optional)
if [ -n "${LANGFUSE_DB_USER:-}" ] && [ -n "${LANGFUSE_DB_PASSWORD:-}" ] && [ -n "${LANGFUSE_DB_NAME:-}" ]; then
	echo "SETUP INFO: Setting up Langfuse database..."
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
		SELECT 'CREATE DATABASE ${LANGFUSE_DB_NAME}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${LANGFUSE_DB_NAME}') \gexec
		DO \$\$
		BEGIN
			IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${LANGFUSE_DB_USER}') THEN
				CREATE USER ${LANGFUSE_DB_USER} WITH PASSWORD '${LANGFUSE_DB_PASSWORD}';
			END IF;
		END
		\$\$;
		GRANT ALL PRIVILEGES ON DATABASE ${LANGFUSE_DB_NAME} TO ${LANGFUSE_DB_USER};
	EOSQL

	# Grant schema permissions on the langfuse database
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${LANGFUSE_DB_NAME}" <<-EOSQL
		GRANT ALL ON SCHEMA public TO ${LANGFUSE_DB_USER};
		ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${LANGFUSE_DB_USER};
		ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${LANGFUSE_DB_USER};
		ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ${LANGFUSE_DB_USER};
	EOSQL
	echo "SETUP INFO: Langfuse database '${LANGFUSE_DB_NAME}' created successfully!"
else
    echo "SETUP INFO: Langfuse database setup skipped (no environment variables provided)"
fi
