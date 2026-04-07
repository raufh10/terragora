package pkg

import (
  "context"
  "testing"
  "fmt"

  "github.com/DATA-DOG/go-sqlmock"
  "github.com/jmoiron/sqlx"
)

func TestBulkIngestRawPosts(t *testing.T) {
  // 1. Setup Mock
  mockDB, mock, err := sqlmock.New()
  if err != nil {
    t.Fatalf("failed to open sqlmock: %s", err)
  }
  defer mockDB.Close()
  db := sqlx.NewDb(mockDB, "postgres")

  // 2. Define Data
  posts := []StorablePost{
    {
      RedditID: "abc_123",
      Title:    "Test Post",
      Content:  "Hello World",
      Metadata: map[string]interface{}{"author": "gemini"},
      IsActive: true,
    },
  }

  // 3. Expectation
  mock.ExpectExec("INSERT INTO reddit_posts").
    WithArgs(
      sqlmock.AnyArg(), // redditIDs
      sqlmock.AnyArg(), // titles
      sqlmock.AnyArg(), // contents
      sqlmock.AnyArg(), // urls
      sqlmock.AnyArg(), // postedAts
      sqlmock.AnyArg(), // metadatas
      sqlmock.AnyArg(), // isActives
    ).
    WillReturnResult(sqlmock.NewResult(1, 1))

  // 4. Execute
  err = BulkIngestRawPosts(context.Background(), db, posts)

  // 5. Assert
  if err != nil {
    t.Errorf("expected no error, got %v", err)
  }

  if err := mock.ExpectationsWereMet(); err != nil {
    t.Errorf("unmet expectations: %s", err)
  }
}

func TestBulkIngestRawPosts_Error(t *testing.T) {
  mockDB, mock, _ := sqlmock.New()
  defer mockDB.Close()
  db := sqlx.NewDb(mockDB, "postgres")

  // Simulate a database connection failure or syntax error
  mock.ExpectExec("INSERT INTO reddit_posts").
    WillReturnError(fmt.Errorf("network partition"))

  err := BulkIngestRawPosts(context.Background(), db, []StorablePost{{RedditID: "123"}})

  if err == nil {
    t.Error("expected an error but got nil")
  }
}
