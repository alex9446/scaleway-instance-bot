from asyncio import gather

from scaleway_async import ALL_ZONES, Client
from scaleway_async.instance.v1.api import InstanceV1API


class Scaleway:
    def __init__(self):
        self.client = Client.from_env()
        self.instance_api = InstanceV1API(self.client)

    async def list_servers(self):
        server = await gather(*[self.instance_api.list_servers_all(zone=zone)
                                for zone in ALL_ZONES])
        return [item for sublist in server for item in sublist]
