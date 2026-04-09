package filters

import (
  "github.com/google/uuid"
)

// PrepareUpdates converts the extracted LLM data into maps ready for DB bulk updates.
func PrepareUpdates(payload *pipeline.PipelinePayload) (map[uuid.UUID]interface{}, map[uuid.UUID]interface{}) {
  postID := payload.Post.ID

  priceUpdate := make(map[uuid.UUID]interface{})
  priceUpdate[postID] = payload.Extraction.Prices

  notesUpdate := make(map[uuid.UUID]interface{})
  notesUpdate[postID] = payload.Extraction.Notes

  return priceUpdate, notesUpdate
}
