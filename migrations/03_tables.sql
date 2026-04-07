-- Create the main table
CREATE TABLE public.reddit_posts (
  id           uuid                     NOT NULL DEFAULT gen_random_uuid(),
  reddit_id    character varying(20)    NOT NULL,
  subreddit_id integer,
  title        text                     NOT NULL,
  content      text,
  url          text,
  price        jsonb,
  posted_at    timestamp with time zone,
  scraped_at   timestamp with time zone DEFAULT now(),
  embedding    vector(1536),
  metadata     jsonb                    DEFAULT '{}'::jsonb,
  is_active    boolean                  NOT NULL DEFAULT true,
  notes        text,

  CONSTRAINT reddit_posts_pkey PRIMARY KEY (id),
  CONSTRAINT reddit_posts_reddit_id_key UNIQUE (reddit_id),
  CONSTRAINT reddit_posts_subreddit_id_fkey 
    FOREIGN KEY (subreddit_id) REFERENCES subreddits(id)
);

