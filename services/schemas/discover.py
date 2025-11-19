from enum import Enum
from typing import Annotated, List
from pydantic import BaseModel, Field, ConfigDict

class Category(BaseModel):
  name: Annotated[str, Field(
    min_length=2,
    max_length=60,
    description="Category name (specific interpretation, e.g., 'roofing_repair_service_request')."
  )]
  confidence: Annotated[float, Field(
    ge=0, le=100,
    description="Confidence score (0–100) estimating how strongly this category applies."
  )]
  reasoning: Annotated[str, Field(
    min_length=5, max_length=160,
    description="One concise sentence explaining the rationale for the categorization."
  )]

class FixedCategory(str, Enum):
  real_estate_agent = "real_estate_agent"
  electrician = "electrician"
  roofing = "roofing"
  mechanic = "mechanic"
  other = "other"

class DiscoverCategory(BaseModel):
  items: Annotated[List[Category], Field(
    min_length=5,
    max_length=5,
    description="Exactly five category interpretations ranked by likelihood or relevance."
  )]
  fixed_category: Annotated[FixedCategory, Field(
    description=(
      "Final simplified category chosen from "
      "{real_estate_agent, electrician, roofing, mechanic, other}, "
      "derived from the most representative/highest-confidence item in `items`. "
      "Use 'other' only if none of the items map clearly to the fixed categories."
    )
  )]

  model_config = ConfigDict(
    json_schema_extra={
      "examples": [
        {
          "items": [
            {
              "name": "roofing_repair_service_request",
              "confidence": 94.2,
              "reasoning": "User explicitly asks for quotes to fix damage on their home's roof."
            },
            {
              "name": "storm_damage_home_restoration",
              "confidence": 88.9,
              "reasoning": "Mentions storm damage and urgency for repair services."
            },
            {
              "name": "contractor_shortlist_evaluation",
              "confidence": 82.3,
              "reasoning": "User is comparing multiple roofing contractors based on cost/quality."
            },
            {
              "name": "trustworthiness_reputation_check",
              "confidence": 74.5,
              "reasoning": "User asks for reviews and reputation info rather than just availability."
            },
            {
              "name": "general_home_repair_discussion",
              "confidence": 63.1,
              "reasoning": "Conversation includes broader advice beyond immediate contracting."
            }
          ],
          "fixed_category": "roofing"
        }
      ]
    }
  )

class SubCategory(str, Enum):
  # Games related
  stats = "stats"
  insights = "insights"
  highlights = "highlights"
  live_thread = "live_thread"
  game_recap = "game_recap"
  referees = "referees"
  game_strategy = "game_strategy"

  # Fan experience
  tickets_related = "tickets_related"
  interaction = "interaction"
  arena_experience = "arena_experience"
  merch = "merch"
  fan_events = "fan_events"

  # Players
  praises = "praises"
  critics = "critics"
  meme = "meme"
  player_stats = "player_stats"
  injury_update = "injury_update"
  player_interview = "player_interview"
  player_development = "player_development"
  contract_discussion = "contract_discussion"

  # Roster
  lineups = "lineups"
  trade = "trade"
  free_agency = "free_agency"
  performance = "performance"
  chemistry = "chemistry"
  rotations = "rotations"
  depth_chart = "depth_chart"
  coaching = "coaching"

  # G-League
  g_league = "g_league"
  g_league_prospect = "g_league_prospect"

  # Media
  podcast = "podcast"
  press_conference = "press_conference"
  sports_panel = "sports_panel"
  analysis_video = "analysis_video"

  # Leagues / other teams
  other_teams = "other_teams"
  league_news = "league_news"
  standings = "standings"
  schedule = "schedule"

  # Throwback
  throwback = "throwback"
  history = "history"
  legends = "legends"

  # Misc
  misc_talk = "misc_talk"
  humor = "humor"
  rant = "rant"
  question = "question"

class SubCategoryItem(BaseModel):
  subcategory: Annotated[SubCategory, Field(
    description="One specific subcategory label for this post."
  )]
  confidence: Annotated[float, Field(
    ge=0, le=100,
    description="Confidence score (0–100) estimating how strongly this subcategory applies."
  )]
  reasoning: Annotated[str, Field(
    min_length=5, max_length=160,
    description="One concise sentence explaining the rationale for this subcategory assignment."
  )]

class NBAThreadCategory(BaseModel):
  subcategories: Annotated[List[SubCategoryItem], Field(
    min_length=1,
    max_length=10,
    description="List of the most relevant subcategory labels for this post, each with confidence and reasoning."
  )]

  model_config = ConfigDict(
    json_schema_extra={
      "examples": [
        {
          "subcategories": [
            {
              "subcategory": "highlights",
              "confidence": 92.5,
              "reasoning": "Post shares a clip of key plays from last night’s game."
            },
            {
              "subcategory": "player_stats",
              "confidence": 88.0,
              "reasoning": "User breaks down box score stats for the starting lineup."
            },
            {
              "subcategory": "praises",
              "confidence": 81.3,
              "reasoning": "Most of the comments are complimenting a specific player’s performance."
            }
          ]
        }
      ]
    }
  )
