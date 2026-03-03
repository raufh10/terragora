from __future__ import annotations
import asyncpraw
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from services.config import configs

@dataclass
class AsyncPrawStarter:
  client_id: str = field(default_factory=lambda: configs.client_id.get_secret_value())
  client_secret: Optional[str] = field(default_factory=lambda: configs.client_secret.get_secret_value())
  user_agent: str = field(default_factory=lambda: configs.USER_AGENT)
  read_only: bool = field(default_factory=lambda: configs.IS_READ_ONLY)
  timeout: float = field(default_factory=lambda: float(configs.TIMEOUT))

  def with_client(self, client_id: str, client_secret: Optional[str] = None) -> AsyncPrawStarter:
    self.client_id = client_id
    self.client_secret = client_secret
    return self

  def with_user_agent(self, user_agent: str) -> AsyncPrawStarter:
    self.user_agent = user_agent
    return self

  def with_timeout(self, seconds: float) -> AsyncPrawStarter:
    self.timeout = seconds
    return self

  def with_read_only(self, read_only: bool = True) -> AsyncPrawStarter:
    self.read_only = read_only
    return self

  @classmethod
  def from_dict(cls, config: dict) -> AsyncPrawStarter:
    return cls(
      client_id=config.get("client_id", configs.client_id),
      client_secret=config.get("client_secret", configs.client_secret),
      user_agent=config.get("user_agent", configs.USER_AGENT),
      read_only=config.get("read_only", configs.IS_READ_ONLY),
      timeout=float(config.get("timeout_seconds", configs.TIMEOUT))
    )

  async def build(self) -> asyncpraw.Reddit:
    if not self.client_id or not self.user_agent:
      raise ValueError("client_id and user_agent are required")

    init_kwargs: Dict[str, Any] = {
      "client_id": self.client_id,
      "client_secret": self.client_secret,
      "user_agent": self.user_agent,
    }

    try:
      from aiohttp import ClientTimeout
      init_kwargs["requestor_kwargs"] = {"timeout": ClientTimeout(total=self.timeout)}
    except ImportError:
      init_kwargs["requestor_kwargs"] = {"timeout": self.timeout}

    reddit = asyncpraw.Reddit(**init_kwargs)
    reddit.read_only = self.read_only
    return reddit
