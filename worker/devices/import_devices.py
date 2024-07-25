#!/usr/bin/env python3
import logging
import typing
from typing import Any
from collections import namedtuple
from sys import argv
from frinx.common.graphql.client import GraphqlClient
from frinx.common.frinx_rest import INVENTORY_URL_BASE, INVENTORY_HEADERS

from frinx_api.inventory import AddDeviceInput, AddDevicePayload, Device, Zone, ZoneEdge, AddDeviceMutation, DeviceServiceState, AddDeviceMutationResponse
from frinx_api.inventory import AddBlueprintPayload, AddBlueprintInput, AddBlueprintMutation, Blueprint, AddBlueprintMutationResponse
from frinx_api.inventory import CreateLabelInput, CreateLabelMutation, CreateLabelPayload, Label
from frinx_api.inventory import Zone, ZoneEdge, ZonesQuery, ZonesConnection
from frinx_api.inventory import ZonesQueryResponse, ZoneEdge, ZonesQuery, ZonesConnection
from frinx_api.inventory import LabelsQuery, LabelConnection, LabelEdge, LabelsQueryResponse, CreateLabelMutationResponse


client = GraphqlClient(endpoint=INVENTORY_URL_BASE, headers=INVENTORY_HEADERS)


def execute(body, variables):
    response = client.execute(query=body, variables=variables)
    if response.get('errors'):
        print("IMPORT DEVICES:", response)
    return response


ZONES_QUERY: ZonesQuery = ZonesQuery(
    payload=ZonesConnection(
        edges=ZoneEdge(
            node=Zone(
                name=True,
                id=True
            )
        )
    )
)

LABEL_MUTATION = CreateLabelMutation(
    payload=CreateLabelPayload(
        label=Label(
            id=True,
            name=True
        )
    ),
    input=CreateLabelInput(
        name=''
    )
)


ADD_BLUEPRINT_MUTATION: AddBlueprintMutation = AddBlueprintMutation(
    payload=AddBlueprintPayload(
        blueprint=Blueprint(
            id=True,
            name=True,
            template=True
        )
    ),
    input=AddBlueprintInput(
        name='',
        template='',
    )
)

LABELS_QUERY: LabelsQuery = LabelsQuery(
    payload=LabelConnection(
        edges=LabelEdge(
            node=Label(
                name=True,
                id=True
            )
        )
    )
)


def main():
    DEVICE_DATA_CSV = argv[1]
    DEVICE_DATA_JSON = argv[2]

    import_devices(DEVICE_DATA_CSV, DEVICE_DATA_JSON)
    import_blueprints(DEVICE_DATA_JSON)


def get_zone_id(zone_name: str) -> str:
    query = ZONES_QUERY.render(form='extracted')
    query_old = ZONES_QUERY.render(form='inline')
    print(query.query, query.variable, query_old)

    response = ZonesQueryResponse(**execute(query.query, query.variable))

    if response.errors is not None:
        raise Exception("Not possible to query device inventory zones")

    for node in response.data.zones.edges:
        if node.node.name == zone_name:
            return node.node.id


def get_label_id(label_name: str) -> str:
    query = LABELS_QUERY.render(form='extracted')
    response = LabelsQueryResponse(**execute(query.query, query.variable))
    if response.errors is not None:
        raise Exception("Not possible to query device inventory labels")

    label_id = None

    for node in response.data.labels.edges:
        if node.node.name == label_name:
            label_id = node.node.id

    if label_id is None:
        LABEL_MUTATION.input.name = label_name
        query = LABEL_MUTATION.render(form='extracted')
        response = CreateLabelMutationResponse(**execute(query.query, query.variable))
        if response.errors is not None:
            raise Exception("Not possible to create device inventory labels")
        if response.data.create_label.label.name == label_name:
            return response.data.create_label.label.id
    else:
        return label_id


def import_blueprints(device_data_json: str):
    with open(device_data_json) as json_file:
        device_import_json = json_file.read()

        ADD_BLUEPRINT_MUTATION.input.template = device_import_json
        ADD_BLUEPRINT_MUTATION.input.name = device_data_json.split("/")[-1].replace("_import.json", "")

        query = ADD_BLUEPRINT_MUTATION.render(form='extracted')
        response = AddBlueprintMutationResponse(**execute(query.query, query.variable))
        if response.errors is not None:
            logging.warning(response.errors)


def build_device_mount_body(device_data_csv: str) -> tuple[list[str], typing.Type[tuple], dict[str, str]]:

    with open(device_data_csv) as data_file:
        all_device_data = data_file.readlines()

    json_replacements = {}

    device_data_header = all_device_data[0].split(',')
    for i in enumerate(device_data_header):
        device_data_header[i[0]] = i[1].strip()

    # create a device_data_def suitable for both cli and netconf device types
    device_data_def = namedtuple('device_data_def', device_data_header)

    # create replacements
    for i in device_data_header:
        key = '{{%s}}' % i
        json_replacements[key] = i

    # skip the first line in csv
    return all_device_data[1:], device_data_def, json_replacements


def import_devices(device_data_csv, device_data_json):

    with open(device_data_json) as json_file:
        device_import_json = json_file.read()

    all_device_data, device_data_def, json_replacements = build_device_mount_body(device_data_csv)

    for device in all_device_data:

        # prepare a list with device data
        data_list = device.strip().split(',')

        # create a dict for easier use
        device_data_tuple = device_data_def(*data_list)
        device_data = dict(device_data_tuple._asdict())

        device_json = device_import_json

        # replace the relevant parts for each device to create a JSON file
        for k in json_replacements.keys():
            val = json_replacements[k]
            device_json = device_json.replace(k, device_data[val])

        ADD_DEVICE_MUTATION: AddDeviceMutation = AddDeviceMutation(
            payload=AddDevicePayload(
                device=Device(
                    id=True,
                    name=True,
                    isInstalled=True,
                    zone=Zone(
                        name=True,
                        id=True
                    )
                )
            ),
            input=AddDeviceInput(
                mountParameters=device_json,
                zoneId=get_zone_id(device_data['zone_name']),
                name=device_data['device_id'],
                serviceState=DeviceServiceState(device_data['service_state'])
            )
        )

        if not device_data['labels'] == '':
            label_ids = []
            for label_name in device_data['labels'].split("|"):
                label_ids.append(get_label_id(label_name))

            ADD_DEVICE_MUTATION.input.label_ids = label_ids

        query = ADD_DEVICE_MUTATION.render(form='extracted')
        print(query.query, query.variable)
        response = AddDeviceMutationResponse(**execute(query.query, query.variable))

        if response.errors is not None:
            logging.warning(response.errors)


if __name__ == '__main__':
    main()
