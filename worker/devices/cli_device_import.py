from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Cli(BaseModel):
    cli_topology_host: str = Field('sample-topology', alias="cli-topology:host")
    cli_topology_port: str = Field('{{port}}', alias='cli-topology:port')
    cli_topology_transport_type: str = Field("ssh", alias='cli-topology:transport-type')
    cli_topology_device_type: str = Field("{{device_type}}", alias='cli-topology:device-type')
    cli_topology_device_version: str = Field("{{device_version}}", alias='cli-topology:device-version')
    cli_topology_password: str = Field("{{password}}", alias='cli-topology:password')
    cli_topology_username: str = Field("{{username}}", alias='cli-topology:username')
    cli_topology_journal_size: int = Field(500, alias='cli-topology:journal-size')
    cli_topology_dry_run_journal_size: int = Field(
        180, alias='cli-topology:dry-run-journal-size'
    )
    cli_topology_parsing_engine: str = Field("tree-parser", alias='cli-topology:parsing-engine')


class Model(BaseModel):
    cli: Optional[Cli] = Cli()
