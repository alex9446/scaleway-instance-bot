from asyncio import gather
from typing import Literal, TypeGuard, get_args
from uuid import UUID

from scaleway_async import ALL_ZONES, Client
from scaleway_async.instance.v1.api import InstanceV1API
from scaleway_async.instance.v1.types import Server, ServerAction

AllowedActions = Literal[
    ServerAction.POWERON, ServerAction.POWEROFF, ServerAction.STOP_IN_PLACE
]
ALLOWED_ACTIONS: set[str] = set(get_args(AllowedActions))


def is_allowed_action(action_to_test: str) -> TypeGuard[AllowedActions]:
    return action_to_test in ALLOWED_ACTIONS


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
        servers = await gather(*[
            self.instance_api.list_servers_all(zone=zone) for zone in ALL_ZONES
        ])
        return [server for zone_servers in servers for server in zone_servers]

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

    async def perform_action(self, action: AllowedActions, server: Server):
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
        action, server_id_or_name = raw_action.split(':', maxsplit=1)
        if not is_allowed_action(action):
            raise ValueError('action not valid')
        server = (
            await self.find_server_by_id(server_id_or_name)
            if is_uuid_v4(server_id_or_name) else
            await self.find_server_by_name(server_id_or_name)
        )
        await self.perform_action(action, server)
        return action
