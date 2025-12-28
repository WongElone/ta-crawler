import logging
from typing import Callable, Any
from psycopg import Error as PsycopgError
from psycopg import IsolationLevel
from psycopg_pool import pool, PoolClosed, PoolTimeout
from psycopg import Cursor
from psycopg.rows import tuple_row
from psycopg_pool import ConnectionPool
from typing import cast

log = logging.getLogger(__name__)

class PsycopgPgClient:
    def __init__(self, user: str, password: str, host: str, port: int, db_name: str):
        self.__user = user
        self.__password = password
        self.__host = host
        self.__port = port
        self.__db_name = db_name
        self.__connection_pool = None
        self.__binary_mode = False

    @property
    def is_connected(self) -> bool:
        def test_query(cursor: Cursor):
            cursor.execute("SELECT 1")
            return cursor.fetchone()
        try:
            result = self.query(test_query)
            log.info(f"Connection test result: {result}")
            return result is not None and result[0] == 1
        except Exception as e:
            log.error(f"Connection test failed: {e}", exc_info=True)
            return False

    def open(self):
        if self.__connection_pool is not None:
            return
        conn_str = f"postgresql://{self.__user}:{self.__password}@{self.__host}:{self.__port}/{self.__db_name}"
        self.__connection_pool = pool.ConnectionPool(conn_str)
        log.info(f"Opened connection pool to postgresql://{self.__host}:{self.__port}/{self.__db_name} with user {self.__user}")

    def close(self):
        if self.__connection_pool is None:
            return
        self.__connection_pool.close()
        self.__connection_pool = None
        log.info(f"Closed connection pool to postgresql://{self.__host}:{self.__port}/{self.__db_name} with user {self.__user}")

    def toggle_binary_mode(self, enabled: bool):
        self.__binary_mode = enabled

    def query[R](self, callback: Callable[[Cursor[Any]], R], row_factory: Callable[[Cursor[Any]], Any] = tuple_row, retry_count: int = 0) -> R:
        """
        Execute a database queries using the provided callback function.
        
        Args:
            callback: A function that takes a psycopg cursor, take some operations and then returns a result of type R if any
            
        Returns:
            The result of the callback if successful, raise an exception if an error occurs
        """

        conn = None
        try:
            if self.__connection_pool is None:
                self.open()
            conn = cast(ConnectionPool, self.__connection_pool).getconn(timeout=2)
            conn.set_autocommit(True)
            with conn.cursor(row_factory=row_factory, binary=self.__binary_mode) as cursor:
                return callback(cursor)
        except (PoolClosed, PoolTimeout) as e:
            self.__connection_pool = None
            if retry_count > 0:
                log.error(f"Database pool closed unexpectedly, retry connect {retry_count} times, still failed")
                raise e
            else:
                log.error(f"Database pool closed unexpectedly, retry connect {retry_count} times")
                self.open()
                return self.query(callback, row_factory, retry_count + 1)
        except PsycopgError as e:
            log.error(f"Database error: {e}", exc_info=True)
            raise e
        finally:
            if conn:
                conn.set_autocommit(False)
                cast(ConnectionPool, self.__connection_pool).putconn(conn)
        

    def txn[R](self, callback: Callable[[Cursor[Any]], R], isolation_lvl: IsolationLevel = IsolationLevel.READ_COMMITTED, row_factory: Callable[[Cursor[Any]], Any] = tuple_row, retry_count: int = 0) -> R:
        """
        Execute a database queries in a single transaction using the provided callback function.
        
        Args:
            callback: A function that takes a psycopg cursor, take some operations and then returns a result of type R if any
            
        Returns:
            The result of the callback if successful, raise an exception if an error occurs
        """

        if isolation_lvl not in [IsolationLevel.READ_COMMITTED, IsolationLevel.REPEATABLE_READ, IsolationLevel.SERIALIZABLE]:
            raise ValueError(f"Not allowed isolation level: {isolation_lvl}")

        conn = None
        try:
            if self.__connection_pool is None:
                self.open()
            conn = cast(ConnectionPool, self.__connection_pool).getconn(timeout=2)
            conn.set_isolation_level(isolation_lvl)
            with conn.transaction():
                with conn.cursor(row_factory=row_factory) as cursor:
                    result = callback(cursor)
                    return result
        except (PoolClosed, PoolTimeout) as e:
            self.__connection_pool = None
            if retry_count > 0:
                log.error(f"Database pool closed unexpectedly, retry connect {retry_count} times, still failed")
                raise e
            else:
                log.error(f"Database pool closed unexpectedly, retry connect {retry_count} times")
                self.open()
                return self.txn(callback, isolation_lvl, row_factory, retry_count + 1)
        except PsycopgError as e:
            log.error(f"Database error: {e}", exc_info=True)
            raise e
        finally:
            if conn:
                conn.set_isolation_level(IsolationLevel.READ_COMMITTED)
                cast(ConnectionPool, self.__connection_pool).putconn(conn)
