from asyncio import gather
from typing import Literal, TypeGuard, get_args
from uuid import UUID

from scaleway_async import ALL_ZONES, Client
from scaleway_async.instance.v1.api import InstanceV1API
from scaleway_async.instance.v1.types import Server, ServerAction

SERVERACTIONS = Literal['poweron', 'poweroff']


def is_action(action_to_test: str) -> TypeGuard[SERVERACTIONS]:
    valid_actions = get_args(SERVERACTIONS)
    return action_to_test in valid_actions


def is_uuid_v4(uuid_to_test: str, version: int = 4) -> TypeGuard[UUID]:
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


class Scaleway:
    def __init__(self):
        self.client = Client.from_env()
        self.instance_api = InstanceV1API(self.client)

    async def list_servers(self):
        server = await gather(*[self.instance_api.list_servers_all(zone=zone)
                                for zone in ALL_ZONES])
        return [item for sublist in server for item in sublist]

    async def find_server_by_id(self, server_id: UUID):
        servers = await self.list_servers()
        server = next((s for s in servers if s.id == server_id), None)
        if not server:
            raise ValueError(f'no server with id: {server_id}')
        return server

    async def find_server_by_name(self, server_name: str):
        servers = await self.list_servers()
        server = next((s for s in servers if s.name == server_name), None)
        if not server:
            raise ValueError(f'no server with name: {server_name}')
        return server

    async def perform_action(self, action: SERVERACTIONS, server: Server):
        server_state = server.state
        if ((action == 'poweron' and server_state != 'stopped') or
                (action == 'poweroff' and server_state != 'running')):
            raise ValueError(f'server is already {server_state}')

        await self.instance_api.server_action(
            action=ServerAction(action),
            server_id=server.id,
            zone=server.zone
        )

    async def perform_raw_action(self, raw_action: str):
        action, server_id = raw_action.split(':', maxsplit=1)
        if not is_action(action):
            raise ValueError('action not valid')
        if not is_uuid_v4(server_id):
            raise ValueError('server_id not valid')
        server = await self.find_server_by_id(server_id)
        await self.perform_action(action, server)
        return action
