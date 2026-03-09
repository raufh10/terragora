-- Function to perform similarity search for RAG
CREATE OR REPLACE FUNCTION match_reddit_items (
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  price NUMERIC,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    reddit_posts.id,
    reddit_posts.title,
    reddit_posts.content,
    reddit_posts.price,
    1 - (reddit_posts.embedding <=> query_embedding) AS similarity
  FROM reddit_posts
  WHERE 1 - (reddit_posts.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;

