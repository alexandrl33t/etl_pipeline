import logging
import time
from typing import Iterator, Optional, Tuple

import backoff
from elasticsearch import Elasticsearch, helpers

from config import BACKOFF_CONFIG, ElasticConfig
from storage import BaseStorage

logger = logging.getLogger(__name__)


class TrackingGenerator:
    def __init__(self, data, itersize, storage, key, index):
        self.data = data
        self.itersize = itersize
        self.storage = storage
        self.key = key
        self.index = index
        self.i = 0
        self.last_modified = ""

    def __iter__(self):
        for movie, modified in self.data:
            self.i += 1
            self.last_modified = modified
            yield {
                "_index": self.index,
                "_id": movie["id"],
                "_source": movie,
            }
            if self.i % self.itersize == 0:
                self.storage.save_state(self.key, self.last_modified)

    def get_last_modified(self):
        return self.last_modified


class ElasticLoader:
    def __init__(
        self,
        config: ElasticConfig,
        storage: BaseStorage,
        elastic_connection: Optional[Elasticsearch] = None,
    ) -> None:
        self._config = config
        self._elastic_connection = elastic_connection
        self._storage = storage

    @property
    def elastic_connection(self) -> Elasticsearch:
        """Вернуть текущее подключение для ES или инициализировать новое"""
        if self._elastic_connection is None or not self._elastic_connection.ping():
            self._elastic_connection = self._create_connection()

        return self._elastic_connection  # type: ignore

    @backoff.on_exception(**BACKOFF_CONFIG)
    def _create_connection(self) -> Elasticsearch:
        """Создать новое подключение для ES"""
        return Elasticsearch([f"{self._config.host}:{self._config.port}"])

    @backoff.on_exception(**BACKOFF_CONFIG)
    def upload_data(
        self, data: Iterator[Tuple[dict, str]], itersize: int, index: str
    ) -> None:
        """Загружает данные в ES используя итератор"""
        t = time.perf_counter()
        key = f"load_from_{index}"

        gen = TrackingGenerator(data, itersize, self._storage, key, index)
        lines, _ = helpers.bulk(
            client=self.elastic_connection,
            actions=gen,
            index=index,
            chunk_size=itersize,
        )

        elapsed = time.perf_counter() - t

        if lines == 0:
            logger.info("Nothing to update for index %s", index)
        else:
            logger.info("%s lines saved in %s for index %s", lines, elapsed, index)
            last_modified = gen.get_last_modified()
            if last_modified:
                self._storage.save_state(key, gen.get_last_modified())
