-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create IVFFlat index for face encodings (will be created after table exists)
-- This is run after migrations
