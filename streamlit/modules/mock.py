def build_mock_analysis():
  return {
    "quick_fit": {
      "likely_match_percent": 84,
      "strengths": ["SQL", "Python", "ETL Pipelines"],
      "missing_areas": ["Airflow DAGs", "dbt"],
      "headline": "Strong data foundations and pipeline experience; add orchestration keywords for a higher score."
    },
    "responsibilities_lite": {
      "coverage_ratio": 0.72,
      "items_top5": [
        {"duty": "Design and maintain ETL pipelines", "status": "covered"},
        {"duty": "Build analytics datasets", "status": "covered"},
        {"duty": "Orchestrate jobs (Airflow/Prefect)", "status": "not_obvious"},
        {"duty": "Implement CI/CD for data workflows", "status": "not_obvious"},
        {"duty": "Collaborate with stakeholders", "status": "covered"}
      ]
    },
    "essential_requirements": {
      "degree_required": True,
      "degree_met": True,
      "experience_required_years": 3,
      "experience_estimated_years": 4.0,
      "experience_met": True
    },
    "skills_overview": {
      "matched_top5": [
        {"name": "Python", "match_type": "exact"},
        {"name": "SQL", "match_type": "exact"},
        {"name": "Pandas", "match_type": "close"},
        {"name": "Data Warehousing", "match_type": "close"},
        {"name": "AWS", "match_type": "close"}
      ],
      "missing_top5": ["Airflow", "dbt", "Snowflake", "Looker", "CI/CD"]
    },
    "keyword_hints": {
      "add_these_terms_top5": ["Airflow DAGs", "dbt models", "Snowflake tasks", "data contracts", "orchestration"]
    },
    "tailor_tip": {
      "suggestion": "Add a bullet that names Airflow/dbt explicitly and quantify a pipeline reliability or runtime improvement.",
      "target_role_title": "Data Engineer",
      "mapped_jd_task": "Own orchestration and model builds"
    }
  }
