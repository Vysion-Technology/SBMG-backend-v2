#!/bin/bash
set -e

# Create database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sbm_rajasthan') THEN
            CREATE DATABASE sbm_rajasthan;
        END IF;
    END
    \$\$;
EOSQL

echo "Database initialization completed."