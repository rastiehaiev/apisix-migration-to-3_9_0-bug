#!/usr/bin/env python
import yaml
import json
import requests

base_url = "http://127.0.0.1:9180/apisix/admin"
auth_token = "VQrwFW9x4Cxjcy"
auth_headers = {
    "X-API-KEY": auth_token
}


def read_file_as_string(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()
    return file_content


def read_spec():
    spec_file_path = "spec.yaml"
    return yaml.safe_load(read_file_as_string(spec_file_path))


def apply_resources(resource_name, resources):
    url = f"{base_url}/{resource_name}s"

    # Create new resources
    for resource in resources:
        response = requests.put(url, json=resource, headers=auth_headers)
        if response.status_code == 201:
            print(f"Created {resource_name} with ID='{resource['id']}'.")
        elif response.status_code == 200:
            print(f"Refreshed {resource_name} with ID='{resource['id']}'.")
        else:
            print(
                f"Failed to create {resource_name} with ID='{resource['id']}'. Request failed: {response.status_code}. Resource:\n{resource}")
            print(response.text)
            exit(1)


def delete_resources(resource_name, resources, attempts_left=5):
    if attempts_left == 0:
        print("Failed to delete resources after multiple retries.")
        exit(1)

    url = f"{base_url}/{resource_name}s"
    existing_resources_response = requests.get(url, headers=auth_headers)
    if existing_resources_response.status_code != 200:
        print(f"Failed to list {resource_name}s. Request failed: {existing_resources_response.status_code}.")
        print(existing_resources_response.text)
        exit(1)

    existing_resources_payload = json.loads(existing_resources_response.text)
    existing_resources = existing_resources_payload.get("list", None)
    if existing_resources:
        resources_ids = [item["id"] for item in resources]
        resources_to_be_deleted = [item["value"] for item in existing_resources if item["value"]["id"] not in resources_ids]

        # Delete obsolete resources
        for resource in resources_to_be_deleted:
            response = requests.delete(f"{url}/{resource['id']}", headers=auth_headers)
            if response.status_code != 200:
                print(
                    f"Failed to delete {resource_name} with ID='{resource['id']}'. Request failed: {response.status_code}.")
                print(response.text)
                exit(1)
            else:
                print(f"Deleted {resource_name} with ID='{resource['id']}'.")
    else:
        # sometimes APISIX returns only one route in response if preceded with route creation;
        # using retries, we are addressing this case
        print("Invalid response from Admin API: " + json.dumps(existing_resources_payload) + ". Trying again...")
        delete_resources(resource_name, resources, attempts_left - 1)


if __name__ == "__main__":
    spec_data = read_spec()

    upstreams = spec_data["upstreams"]
    services = spec_data["services"]
    routes = spec_data["routes"]

    # route depends on service, service depends on upstream,
    # that's why we first create resources: upstreams -> services -> routes
    # and then delete them: routes -> services -> upstreams

    apply_resources(resource_name="upstream", resources=upstreams)
    apply_resources(resource_name="service", resources=services)
    apply_resources(resource_name="route", resources=routes)

    delete_resources(resource_name="route", resources=routes)
    delete_resources(resource_name="service", resources=services)
    delete_resources(resource_name="upstream", resources=upstreams)

    # create certificates
    ssls = spec_data["ssls"]
    for ssl in ssls:
        ssl["cert"] = read_file_as_string(ssl["cert"])
        ssl["key"] = read_file_as_string(ssl["key"])

    apply_resources(resource_name="ssl", resources=ssls)
    delete_resources(resource_name="ssl", resources=ssls)
