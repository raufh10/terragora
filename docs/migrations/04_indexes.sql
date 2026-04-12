-- Optimized indexes for search and filtering
CREATE INDEX idx_reddit_posts_is_active 
  ON public.reddit_posts (is_active) 
  WHERE (is_active = true);

CREATE INDEX idx_reddit_posts_metadata 
  ON public.reddit_posts USING gin (metadata);

CREATE INDEX idx_reddit_posts_price 
  ON public.reddit_posts (price) 
  WHERE (price IS NOT NULL);

CREATE INDEX reddit_posts_embedding_idx 
  ON public.reddit_posts USING hnsw (embedding vector_cosine_ops);

