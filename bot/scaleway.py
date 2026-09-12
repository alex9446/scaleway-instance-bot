from asyncio import gather
from os import getenv
from typing import Literal, TypeGuard, get_args
from uuid import UUID

from scaleway_async import ALL_REGIONS, ALL_ZONES, Client
from scaleway_async.container.v1beta1.api import ContainerV1Beta1API
from scaleway_async.instance.v1.api import InstanceV1API
from scaleway_async.instance.v1.types import Server, ServerAction
from scaleway_core.api import ScalewayException

from .utils import logger

AllowedActions = Literal[
    ServerAction.POWERON, ServerAction.POWEROFF,
    ServerAction.REBOOT, ServerAction.STOP_IN_PLACE
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
        self.container_api = ContainerV1Beta1API(self.client)

    async def list_servers(self):
        # workaround for
        # https://github.com/scaleway/scaleway-sdk-python/pull/2161
        FIX_ZONES = ALL_ZONES + ['it-mil-1']
        servers = await gather(*[
            self.instance_api.list_servers_all(zone=zone) for zone in FIX_ZONES
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
        try:
            await self.instance_api.server_action(
                action=ServerAction(action),
                server_id=server.id,
                zone=server.zone
            )
        except ScalewayException as e:
            try:
                raise ValueError(e.response.json()['help_message'])
            except KeyError:
                raise ValueError('ScalewayException occurred')

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

    async def list_containers(self, namespace_id: str):
        containers = await gather(*[
            self.container_api.list_containers_all(
                namespace_id=namespace_id,
                region=region
            ) for region in ALL_REGIONS
        ], return_exceptions=True)
        return [
            container for zone_c in containers
            if not isinstance(zone_c, BaseException)
            for container in zone_c
        ]


async def redeploy_itself():
    scw = Scaleway()
    namespace_id = getenv('SCW_NAMESPACE_ID')
    container_id = getenv('SCW_APPLICATION_ID')
    if not (namespace_id and container_id):
        logger.error('one of SCW_ variables is None')
        return
    containers = await scw.list_containers(namespace_id)
    container = next((c for c in containers if c.id == container_id), None)
    if not container:
        logger.error('not found container with id %s', container_id)
        return
    return await scw.container_api.deploy_container(container_id=container.id,
                                                    region=container.region)


async def try_redeploy() -> tuple[bool, str]:
    if container := await redeploy_itself():
        return (True, f'started redeploy of {container.name}')
    return (False, 'error during redeploy, see logs')
