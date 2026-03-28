-- 1. Add the column with a default value. 
ALTER TABLE reddit_posts 
ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;

-- 2. Add a partial index.
CREATE INDEX idx_reddit_posts_is_active 
ON reddit_posts (is_active) 
WHERE is_active = true;
