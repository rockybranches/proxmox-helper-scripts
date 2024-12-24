import os
import argparse
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict, fields
import json


# Path to the PCI mapping configuration file
CONFIG_FILE = "/etc/pve/mapping/pci.cfg"


@dataclass
class DeviceAttrs:
    id: str = 'unknown'
    iommugroup: int = -1
    node: str = 'unknown'
    path: str = ':::'
    subsystem_id: str = ':'


DEVICE_ATTR_NAMES = [field.name for field in fields(DeviceAttrs())]


def get_pci_devices():
    """
    Retrieve PCI device information dynamically using lspci.
    Returns a list of dictionaries containing PCI device details.

    Expected PCI device attributes:
        - id
        - iommugroup
        - node
        - path
        - subsystem-id
    """
    pci_devices = []
    try:
        # Use 'lspci -vmm' to get detailed information about all PCI devices
        output = subprocess.check_output(["lspci", "-vmm"], text=True)
        # get the node name (hostname)
        node = subprocess.check_output(["hostname"], text=True).strip()
        for device_section in output.split("\n\n"):
            device_attrs = DeviceAttrs(node=node)
            device_name = "<Unknown>"
            for line in device_section.splitlines():
                attr_name, attr_value = line.split("\t")
                attr_name = attr_name.split(":")[0].lower().replace("_", "-")
                if attr_name == 'slot':
                    attr_name = 'path'  # to match syntax of pci.cfg
                if attr_name == "device":
                    device_name = attr_value
                if attr_name in DEVICE_ATTR_NAMES:
                    setattr(device_attrs, attr_name, attr_value)
            pci_devices.append({device_name: asdict(device_attrs)})
    except Exception as e:
        print(f"Error retrieving PCI devices: {e}")
    return pci_devices


def read_pci_config(file_path):
    """
    Read the existing PCI mapping configuration file.
    Returns a dictionary with device names as keys and their mappings as values.
    """
    config = {}
    if not os.path.exists(file_path):
        return config

    try:
        with open(file_path, "r") as f:
            current_device = None
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if not line.startswith("\t"):  # Device name
                    current_device = line.strip()
                    config[current_device] = {}
                else:  # Mapping details
                    key, value = line.strip().split("=", 1)
                    config[current_device][key.strip()] = value.strip()
    except Exception as e:
        print(f"Error reading PCI configuration file: {e}")

    return config


def update_pci_config(pci_devices, current_config, dry_run=False):
    """
    Update the PCI mapping configuration with dynamically retrieved parameters.
    Overwrites the file unless dry_run is True.
    """
    # get the current config values
    current_config = read_pci_config(CONFIG_FILE)
    # extract 'device_name':'id'
    current_device_ids = {}
    for device, attrs in current_config.items():
        current_device_ids[attrs['id']] = device
    
    if len(current_config) == 0:
        print('Warning: No current device mappings are defined, so no configurations will be updated.')
    
    # get the up-to-date device info (namely the corrected path)
    updated_config_list = get_pci_devices()
    
    # get the list as an id-matched dictionary
    def get_matching_device_name(device_id, current_device_ids=current_device_ids):
        for device_name, current_device_id in current_device_ids.items():
            if device_id == current_device_id:
                return device_name
        return None
    
    # first get updated as a dictionary (dropping the human-readable device name)
    updated_configd = {}
    for udict in updated_config_list:
        updated_configd.update({udict['id']: udict})
    # then use the matching device name (as defined in pci.cfg)
    updated_config = {}
    for device_id, device_attrs in updated_configd:
        if device_id not in set(current_device_ids.keys()):
            # skip non-matching device ID
            continue
        # otherwise, map the updated attributes to the matching device name (from pci.cfg)
        updated_config[current_device_ids[device_id]] = device_attrs

    def format_mappings(mappings):
        # stringify the device attributes
        return ",".join([f"{key}={value}" for key, value in mappings.items()])

    if dry_run:
        print("Dry run enabled. The following changes would be made:")
        for device, mappings in updated_config.items():
            print(f"{device}\n\t")
            print(format_mappings(mappings=mappings))
        return

    try:
        with open(CONFIG_FILE, "w") as f:
            for device, mappings in updated_config.items():
                f.write(f"{device}\n\t")
                attrs = format_mappings(mappings=mappings)
                f.write(f"map {attrs}\n\n")
        print(f"PCI configuration updated successfully in {CONFIG_FILE}")
    except Exception as e:
        print(f"Error writing to configuration file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Update PCI mappings for Proxmox VE.")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate updates without modifying the configuration file.",
    )
    parser.add_argument(
        "--print-pci-info",
        action="store_true",
        help="Print detailed information about detected PCI devices.",
    )

    args = parser.parse_args()

    # Retrieve current PCI devices
    pci_devices = get_pci_devices()

    if args.print_pci_info:
        print("Detected PCI Devices:")
        print(json.dumps(pci_devices, indent=3))
        return

    # Read existing configuration
    current_config = read_pci_config(CONFIG_FILE)

    # Update or simulate updating the configuration
    update_pci_config(pci_devices, current_config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
