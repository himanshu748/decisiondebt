from threading import RLock
from time import perf_counter
from falkordb import FalkorDB
from redis.exceptions import ConnectionError, TimeoutError
from backend.app.settings import settings

LOCK = RLock()


class GraphUnavailable(Exception):
    pass


class DomainError(Exception):
    def __init__(self, code, message, status=400):
        self.code = code
        self.message = message
        self.status = status


class Graph:
    def __init__(self, name=None, port=None):
        try:
            self.db = FalkorDB(
                host=settings.host,
                port=port or settings.port,
                socket_timeout=3,
                socket_connect_timeout=2,
            )
        except (ConnectionError, TimeoutError, OSError) as e:
            raise GraphUnavailable() from e
        self.g = self.db.select_graph(name or settings.graph_name)

    def read(self, cypher, params=None, query_id="READ", trace=None):
        start = perf_counter()
        try:
            result = self.g.ro_query(cypher, params or {})
            names = [x[1] for x in result.header]
            rows = [dict(zip(names, r)) for r in result.result_set]
        except (ConnectionError, TimeoutError, OSError) as e:
            raise GraphUnavailable() from e
        if trace is not None:
            trace.append(
                dict(
                    query_id=query_id,
                    cypher=cypher,
                    params=params or {},
                    row_count=len(rows),
                    elapsed_ms=round((perf_counter() - start) * 1000, 3),
                )
            )
        return rows

    def write(self, cypher, params=None):
        try:
            return self.g.query(cypher, params or {})
        except (ConnectionError, TimeoutError, OSError) as e:
            raise GraphUnavailable() from e

    def revision(self):
        rows = self.read(
            "MATCH (m:Meta {key:'graph_revision'}) RETURN m.value AS revision",
            query_id="Q9",
        )
        return int(rows[0]["revision"]) if rows else 0

    def bump(self):
        self.write("MATCH (m:Meta {key:'graph_revision'}) SET m.value=m.value+1")

    def health(self):
        try:
            self.db.connection.ping()
        except (ConnectionError, TimeoutError, OSError) as e:
            raise GraphUnavailable() from e
        return self.revision()
