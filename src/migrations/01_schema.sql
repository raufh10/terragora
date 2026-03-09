-- Table to manage different buy/sell subreddits
CREATE TABLE IF NOT EXISTS subreddits (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    last_scraped_at TIMESTAMP WITH TIME ZONE
);

-- Main table for used items and RAG data
CREATE TABLE IF NOT EXISTS reddit_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reddit_id VARCHAR(20) UNIQUE NOT NULL, 
    subreddit_id INTEGER REFERENCES subreddits(id),
    title TEXT NOT NULL,
    content TEXT,
    url TEXT,
    price NUMERIC(10, 2),
    posted_at TIMESTAMP WITH TIME ZONE,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Embedding column (Dimensions set to 1536 for OpenAI/Standard models)
    embedding vector(1536), 
    
    -- JSONB for flexible metadata (e.g., item condition, location)
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_reddit_posts_subreddit_id ON reddit_posts(subreddit_id);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_price ON reddit_posts(price) WHERE price IS NOT NULL;

-- Vector Index for Semantic Search (HNSW for speed)
CREATE INDEX IF NOT EXISTS reddit_posts_embedding_idx 
ON reddit_posts USING hnsw (embedding vector_cosine_ops);

