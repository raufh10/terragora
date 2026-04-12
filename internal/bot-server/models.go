package botserver

// Update represents a Telegram incoming webhook update
type Update struct {
  Message struct {
    Chat struct {
      ID int64 `json:"id"`
    } `json:"chat"`
    From struct {
      Username string `json:"username"`
    } `json:"from"`
    Text string `json:"text"`
  } `json:"message"`
}
