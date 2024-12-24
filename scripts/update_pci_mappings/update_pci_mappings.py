import os
import argparse
import subprocess
from pathlib import Path

# Path to the PCI mapping configuration file
CONFIG_FILE = "/etc/pve/mapping/pci.cfg"

def get_pci_devices():
    """
    Retrieve PCI device information dynamically using lspci.
    Returns a list of dictionaries containing PCI device details.
    """
    pci_devices = []
    try:
        # Use 'lspci -nn' to get detailed information about all PCI devices
        output = subprocess.check_output(["lspci", "-nn"], text=True)
        for line in output.splitlines():
            parts = line.split()
            slot = parts[0]  # PCI slot (e.g., 04:00.0)
            name = " ".join(parts[1:-1])  # Device name
            ids = parts[-1].strip("[]")  # Vendor and device ID (e.g., 10de:2882)
            pci_devices.append({"slot": slot, "name": name, "ids": ids})
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
    updated_config = {}
    
    for device in pci_devices:
        device_name = device["name"]
        slot = device["slot"]
        ids = device["ids"]
        iommugroup = "unknown"  # Placeholder for IOMMU group (extend logic if needed)
        node = os.uname().nodename
        path = slot.replace(".", "")  # Format path as '0000:04:00'
        
        updated_config[device_name] = {
            "id": ids,
            "iommugroup": iommugroup,
            "node": node,
            "path": path,
            "subsystem-id": ids,
        }

    if dry_run:
        print("Dry run enabled. The following changes would be made:")
        for device, mappings in updated_config.items():
            print(f"{device}")
            for key, value in mappings.items():
                print(f"\t{key}={value}")
        return
    
    try:
        with open(CONFIG_FILE, "w") as f:
            for device, mappings in updated_config.items():
                f.write(f"{device}\n")
                for key, value in mappings.items():
                    f.write(f"\t{key}={value}\n")
        print(f"PCI configuration updated successfully in {CONFIG_FILE}")
    except Exception as e:
        print(f"Error writing to configuration file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Update PCI mappings for Proxmox VE.")
    
    parser.add_argument("--dry-run", action="store_true", help="Simulate updates without modifying the configuration file.")
    parser.add_argument("--print-pci-info", action="store_true", help="Print detailed information about detected PCI devices.")
    
    args = parser.parse_args()

    # Retrieve current PCI devices
    pci_devices = get_pci_devices()

    if args.print_pci_info:
        print("Detected PCI Devices:")
        for device in pci_devices:
            print(f"{device['slot']} - {device['name']} [{device['ids']}]")
        return

    # Read existing configuration
    current_config = read_pci_config(CONFIG_FILE)

    # Update or simulate updating the configuration
    update_pci_config(pci_devices, current_config, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
