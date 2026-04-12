-- Create the trigger function independently
CREATE OR REPLACE FUNCTION notify_reddit_posts_inserted()
RETURNS TRIGGER AS $$BEGIN
  -- Placeholder for notification logic
  -- Example: PERFORM pg_notify('new_post', row_to_json(NEW)::text);
  RETURN NEW;
END;$$ LANGUAGE plpgsql;

