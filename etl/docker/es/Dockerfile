FROM elasticsearch:9.0.2

ENV discovery.type=single-node
ENV xpack.security.enabled=false

COPY preload.sh genres.json persons.json movies.json /
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

USER root
RUN chmod +x /preload.sh /usr/local/bin/entrypoint.sh

USER elasticsearch


ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
