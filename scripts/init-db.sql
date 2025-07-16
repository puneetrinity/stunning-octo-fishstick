-- Initialize database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database for tests
CREATE DATABASE chatseo_test;
GRANT ALL PRIVILEGES ON DATABASE chatseo_test TO chatseo;