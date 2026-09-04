#!/bin/bash
# Razorpay Chargeback AI - PostgreSQL Initialization
# Runs automatically from /docker-entrypoint-initdb.d/ on fresh volume
set -e

echo "======================================================"
echo "Razorpay Chargeback AI - Database Initialization"
echo "======================================================"

echo "[1/3] Enabling pgvector..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS vector;"
echo "    pgvector enabled."

echo "[2/3] Creating application schema..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/00_schema.sql
echo "    Schema created."

echo "[3/3] Loading demo seed data..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/02_seed.sql
echo "    Demo data loaded."

echo "======================================================"
echo "Database initialization complete."
echo "======================================================"
