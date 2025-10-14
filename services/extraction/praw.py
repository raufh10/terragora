from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from services.config import settings, credentials

class PrawStarter:
  def __init__(self, logger):
    self.logger = logger
    self.client_id = credentials.CLIENT_ID
    self.client_secret = credentials.CLIENT_SECRET
    self.user_agent = settings.USER_AGENT
    self.read_only = settings.IS_READ_ONLY
    self.timeout_seconds = settings.TIMEOUT
    self.logger.debug("PrawStarter initialized")

  def with_client(self, client_id: str, client_secret: str = None) -> PrawStarter:
    self.client_id = client_id
    self.client_secret = client_secret
    self.logger.debug("Client credentials configured")
    return self

  def with_user_agent(self, user_agent: str) -> PrawStarter:
    self.user_agent = user_agent
    self.logger.debug("User agent set")
    return self

  def with_timeout(self, seconds: float) -> PrawStarter:
    self.timeout_seconds = seconds
    self.logger.debug(f"Timeout set to {seconds} seconds")
    return self

  def with_read_only(self, read_only: bool = True) -> PrawStarter:
    self.read_only = read_only
    self.logger.debug(f"Read-only mode set to {read_only}")
    return self

  @classmethod
  def from_dict(cls, config: dict, logger) -> PrawStarter:
    inst = cls(logger)
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    user_agent = config.get("user_agent")
    read_only = config.get("read_only")
    timeout_seconds = config.get("timeout_seconds")

    if client_id:
      inst.with_client(client_id, client_secret)
    if user_agent:
      inst.with_user_agent(user_agent)
    if read_only is not None:
      inst.with_read_only(bool(read_only))
    if timeout_seconds is not None:
      inst.with_timeout(float(timeout_seconds))

    inst.logger.debug("Configuration loaded from dictionary")
    return inst

  def _validate(self):
    if not self.client_id:
      raise ValueError("Missing required field: client_id")
    if not self.user_agent:
      raise ValueError("Missing required field: user_agent")

  def build(self):
    try:
      import praw
    except ImportError as e:
      raise RuntimeError("praw not installed. Run: pip install praw") from e

    self._validate()

    init_kwargs = {
      "client_id": self.client_id,
      "user_agent": self.user_agent,
    }
    if self.client_secret:
      init_kwargs["client_secret"] = self.client_secret
    if self.timeout_seconds:
      init_kwargs["requestor_kwargs"] = {"timeout": self.timeout_seconds}

    self.logger.info("Creating praw.Reddit client (read-only mode)")
    reddit = praw.Reddit(**init_kwargs)
    reddit.read_only = self.read_only
    self.logger.debug("praw.Reddit client ready")
    return reddit

  def __repr__(self):
    state = {
      "client_id": bool(self.client_id),
      "client_secret": bool(self.client_secret),
      "user_agent": self.user_agent,
      "read_only": self.read_only,
      "timeout_seconds": self.timeout_seconds,
    }
    return f"PrawStarter({state})"