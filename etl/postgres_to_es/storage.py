import abc
import json
from typing import Optional, Dict, Any

import backoff
from redis import Redis

from config import BACKOFF_CONFIG, RedisConfig


def is_redis_available(redis_conn: Redis) -> bool:
    try:
        redis_conn.ping()
    except Exception:
        return False
    return True


class BaseStorage(abc.ABC):
    """Абстрактное хранилище состояния.

    Позволяет сохранять и получать состояние.
    Способ хранения состояния может варьироваться в зависимости
    от итоговой реализации. Например, можно хранить информацию
    в базе данных или в распределённом файловом хранилище.
    """

    @abc.abstractmethod
    def save_state(self, key: str, state: str) -> None:
        """Сохранить состояние в хранилище."""

    @abc.abstractmethod
    def retrieve_state(self, key: str) -> Dict[str, Any]:
        """Получить состояние из хранилища."""


class RedisStorage(BaseStorage):
    """Реализация хранилища, использующего Redis."""

    def __init__(self, config: RedisConfig, redis_conn: Optional[Redis] = None) -> None:
        self._config = config
        self._redis_connection = redis_conn

    @property
    def redis_connection(self) -> Redis:
        """Использует текущее соединение или создает новое"""
        if not self._redis_connection or not is_redis_available(self._redis_connection):
            self._redis_connection = self._create_connection()
        return self._redis_connection  # type: ignore

    @backoff.on_exception(**BACKOFF_CONFIG)
    def _create_connection(self) -> Redis:
        """Создает новое соединение к Redis"""
        return Redis(**self._config.dict())

    @backoff.on_exception(**BACKOFF_CONFIG)
    def save_state(self, key: str, state: str) -> None:
        """Сохранить состояние в Redis."""
        try:
            json_state = json.dumps(state)
            self.redis_connection.set(key, json_state)
        except Exception as e:
            raise RuntimeError(f"Ошибка при сохранении состояния в Redis: {e}")

    @backoff.on_exception(**BACKOFF_CONFIG)
    def retrieve_state(self, key: str) -> Dict[str, Any]:
        """Получить состояние из Redis."""
        try:
            data = self.redis_connection.get(key)
            if data is None:
                return {}
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return {}
