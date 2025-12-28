from typing import Any, Optional, Callable, Awaitable
import asyncpg
from asyncpg.exceptions import PostgresError, InterfaceError
from asyncpg.pool import PoolConnectionProxy

import logging

log = logging.getLogger(__name__)

class AsyncpgPgClient:
    def __init__(self, user: str, password: str, host: str, port: int, db_name: str):
        self.__user = user
        self.__password = password
        self.__host = host
        self.__port = port
        self.__db_name = db_name
        self.__pool: Optional[asyncpg.pool.Pool] = None

    async def test_connection(self) -> bool:
        """
        Test connection to the database
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            result = await self.fetch("SELECT 1 AS test", lambda record: record['test'])
            return result is not None and len(result) > 0 and result[0] == 1
        except Exception as e:
            log.error(f"Failed to test connection: {e}", exc_info=True)
            return False

    def pool_is_closing(self) -> bool:
        if self.__pool is None:
            return False
        return self.__pool.is_closing()

    async def open(self):
        if self.__pool is not None:
            return
        try:
            self.__pool = await asyncpg.create_pool(
                user=self.__user,
                password=self.__password,
                host=self.__host,
                port=self.__port,
                database=self.__db_name,
                max_size=10
            )
        except Exception as e:
            log.error(f"Failed to open connection pool: {e}", exc_info=True)
            raise e

    async def close(self):
        if self.__pool is None:
            return
        await self.__pool.close()

    async def __on_conn[R](self, callback: Callable[[PoolConnectionProxy], Awaitable[R]]) -> R:
        if self.__pool is None:
            await self.open()
            if self.__pool is None:
                raise Exception("failed to init connection pool")
        try:
            async with self.__pool.acquire() as conn:
                return await callback(conn)
        except PostgresError as e:
            log.error(f"DB Error: {e}", exc_info=True)
            raise e
        except InterfaceError as e:
            log.error(f"Interface Error: {e}", exc_info=True)
            raise e

    async def fetch[R](self, query_str: str, result_mapper: Callable[[dict[str, Any]], R], *params, batch_mode=False, batch_size=5000) -> list[R]:
        if self.__pool is None:
            await self.open()
            if self.__pool is None:
                raise Exception("failed to init connection pool")

        if batch_mode:
            async def callback(conn: PoolConnectionProxy) -> list[R]:
                async with conn.transaction():
                    cursor = await conn.cursor(query_str, *params)
                    result = []
                    while True:
                        batch = await cursor.fetch(batch_size)
                        if not batch:
                            break
                        result.extend(list(map(result_mapper, batch)))
                    return result
            return await self.__on_conn(callback)
        else:
            records = await self.__on_conn(lambda conn: conn.fetch(query_str, *params))
            return list(map(result_mapper, records))

    async def execute(self, query_str: str, *params):
        async def callback(conn: PoolConnectionProxy):
            async with conn.transaction():
                await conn.execute(query_str, *params)
        return await self.__on_conn(callback)

    async def executemany(self, query_str: str, params_list: list[tuple]):
        async def callback(conn: PoolConnectionProxy):
            async with conn.transaction():
                await conn.executemany(query_str, params_list)
        return await self.__on_conn(callback)
