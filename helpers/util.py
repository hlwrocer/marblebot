import asyncio

class Timer:
    def __init__(self, timeout, callback, *callbackArgs):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())
        self._args = callbackArgs

    async def _job(self):
        print('timer started')
        await asyncio.sleep(self._timeout)
        await self._callback(*self._args)

    def cancel(self):
        self._task.cancel()

def getRole(guild, name):
    for role in guild.roles:
        if name == str(role.name):
            return role
    return None

