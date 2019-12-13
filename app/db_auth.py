from aiohttp_security.abc import AbstractAuthorizationPolicy
import models
from security import check_password_hash


class DBAuthorizationPolicy(AbstractAuthorizationPolicy):

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def authorized_userid(self, identity):
        async with self.db_pool.acquire() as conn:
            user = await models.get_user_by_name(conn, identity)
            if user:
                return identity
        return None

    async def permits(self, identity, permission, context=None):
        if identity is None:
            return False
        async with self.db_pool.acquire() as conn:
            user = await models.get_user_by_name(conn, identity)
            if user:
                permission_name = str(user.get('role'))
                if permission_name == permission:
                    return True
        return False