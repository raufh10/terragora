-- Apply the trigger to the table
CREATE TRIGGER reddit_posts_insert_trigger
  AFTER INSERT ON public.reddit_posts
  FOR EACH ROW
  EXECUTE FUNCTION notify_reddit_posts_inserted();

