import logging
import time
from typing import Iterator, Optional, Tuple

import backoff
from elasticsearch import Elasticsearch, helpers

from config import BACKOFF_CONFIG, ElasticConfig
from storage import BaseStorage

logger = logging.getLogger(__name__)


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

    def _generate_docs(
        self, data: Iterator[Tuple[dict, str]], itersize: int, index: str
    ) -> Tuple[Iterator[dict], str]:
        """
        Генерирует документы для bulk-загрузки в Elasticsearch.
        Каждые `itersize` записей сохраняет последний modified в storage.
        Возвращает генератор и последний modified (для финального сохранения после успешной загрузки).
        """
        i = 0
        last_modified = ""
        key = f"load_from_{index}"

        def generator():
            nonlocal i, last_modified
            for movie, modified in data:
                i += 1
                last_modified = modified

                yield {
                    "_index": index,
                    "_id": movie["id"],
                    "_source": movie,
                }

                if i % itersize == 0:
                    self._storage.save_state(key, last_modified)
                    logger.debug(
                        "Saved state after %d items: %s = %s", i, key, last_modified
                    )

        return generator(), last_modified

    @backoff.on_exception(**BACKOFF_CONFIG)
    def upload_data(
        self, data: Iterator[Tuple[dict, str]], itersize: int, index: str
    ) -> None:
        """Загружает данные в ES используя итератор"""
        t = time.perf_counter()
        key = f"load_from_{index}"

        docs_generator, last_modified = self._generate_docs(data, itersize, index)

        lines, _ = helpers.bulk(
            client=self.elastic_connection,
            actions=docs_generator,
            index=index,
            chunk_size=itersize,
        )

        elapsed = time.perf_counter() - t

        if lines == 0:
            logger.info("Nothing to update for index %s", index)
        else:
            logger.info("%s lines saved in %s for index %s", lines, elapsed, index)

            # Финальное сохранение состояния только после успешной загрузки
            if last_modified:
                self._storage.save_state(key, last_modified)
                logger.debug("Final state saved: %s = %s", key, last_modified)
