import os
import configparser
import subprocess
import sys
import json

# Path to the PCI mapping configuration file
CONFIG_FILE = "/etc/pve/mapping/pci.cfg"

def get_pci_devices():
    """
    Retrieve PCI device information dynamically using lspci and other tools.
    Returns a list of dictionaries containing PCI device details.
    """
    pci_devices = []
    try:
        # Use 'lspci -vmm' to get detailed information about all PCI devices
        output = subprocess.check_output(["lspci", "-vmm"], text=True)
        device_info = {}
        for line in output.splitlines():
            if line.strip() == "":
                # End of a device block, save the current device info
                if device_info:
                    pci_devices.append(device_info)
                    device_info = {}
            else:
                key, value = line.split(":", 1)
                device_info[key.strip()] = value.strip()
        if device_info:  # Add last device if not already added
            pci_devices.append(device_info)
    except Exception as e:
        print(f"Error retrieving PCI devices: {e}")
    return pci_devices

def update_pci_config(args):
    """
    Update the PCI mapping configuration file with dynamically retrieved parameters.
    """
    # Ensure the configparser uses a case-sensitive option for keys
    config = configparser.ConfigParser(allow_no_value=True, delimiters=("="))
    config.optionxform = str  # Preserve case sensitivity of keys

    # Read existing configuration if it exists
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)

    # Get current PCI devices
    pci_devices = get_pci_devices()
    if len(args) == 1:
      pass
    else:
      # handle dry-run parameter
      if args[1] in ['--dryrun', '-D']:
        print('**Dry-run specified (no configuration files will be updated).**')
        print()
        print('Up-to-date PCI Device Info:')
        print(json.dumps(pci_devices, indent=3))
        print()
        exit(0)

    # Update or add new entries for each PCI device
    for device in pci_devices:
        id_value = device.get("Slot", "unknown").replace(":", "_")  # Use Slot as ID (e.g., 00:1f.2 -> 00_1f_2)
        iommugroup = "unknown"  # Placeholder: Replace with actual logic to retrieve IOMMU group
        node = os.uname().nodename  # Current node name
        path = f"/sys/bus/pci/devices/{device.get('Slot', '')}"  # Path to the PCI device
        subsystem_id = device.get("Device", "unknown")  # Subsystem ID (e.g., Device name)

        # Update or create section for this PCI device
        config[id_value] = {
            "id": id_value,
            "iommugroup": iommugroup,
            "node": node,
            "path": path,
            "subsystem-id": subsystem_id,
        }

    # Write updated configuration back to file
    try:
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        print(f"PCI configuration updated successfully in {CONFIG_FILE}")
    except Exception as e:
        print(f"Error writing to configuration file: {e}")

if __name__ == "__main__":
    update_pci_config(sys.argv)
