# **PCI Mapping Updater for Proxmox VE**

This repository contains a Python script and a systemd service designed to dynamically update the PCI device mappings in `/etc/pve/mapping/pci.cfg` for Proxmox VE. The script retrieves current PCI device information, updates all relevant parameters (`id`, `iommugroup`, `node`, `path`, and `subsystem-id`), and overwrites the configuration file with the updated data. The systemd service ensures this process runs automatically during boot.

---

## **Features**
- Dynamically retrieves PCI device details using `lspci`.
- Updates or adds entries in `/etc/pve/mapping/pci.cfg` with:
  - **id**: Unique identifier for the PCI device.
  - **iommugroup**: Placeholder (can be extended to retrieve actual IOMMU group information).
  - **node**: The hostname of the current node.
  - **path**: Path to the PCI device in `/sys/bus/pci/devices`.
  - **subsystem-id**: Subsystem identifier (e.g., device name).
- Overwrites the configuration file to ensure it reflects the latest hardware state.
- Integrated with systemd to run automatically at boot.

---

## **Prerequisites**
1. **Proxmox VE Environment**: Ensure you are running Proxmox VE, as this script is tailored for its configuration structure.
2. **Python 3.x**: The script requires Python 3.x to execute.
3. **System Utilities**:
   - `lspci`: Used to retrieve detailed PCI device information.
   - Root privileges are required to modify `/etc/pve/mapping/pci.cfg`.

---

## **Installation and Usage**

### **1. Deploy the Python Script**
1. Save the following script as `/usr/local/bin/update_pci_mappings.py`:

   ```bash
   sudo nano /usr/local/bin/update_pci_mappings.py
   ```

   Copy and paste the Python script from this repository into the file.

2. Make the script executable:
   ```bash
   chmod +x /usr/local/bin/update_pci_mappings.py
   ```

3. Test the script manually:
   ```bash
   sudo /usr/local/bin/update_pci_mappings.py
   ```
   This will update `/etc/pve/mapping/pci.cfg` with dynamically retrieved PCI device information.

---

### **2. Create a Systemd Service**

1. Create a new systemd service file:
   ```bash
   sudo nano /etc/systemd/system/update-pci-mappings.service
   ```

2. Add the following configuration:

   ```ini
   [Unit]
   Description=Update PCI Mappings for Proxmox VE
   After=network.target local-fs.target
   Requires=network.target

   [Service]
   Type=oneshot
   ExecStart=/usr/local/bin/update_pci_mappings.py

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable update-pci-mappings.service
   sudo systemctl start update-pci-mappings.service
   ```

4. Verify that the service executed successfully:
   ```bash
   sudo systemctl status update-pci-mappings.service
   ```

5. Check logs for any errors:
   ```bash
   journalctl -u update-pci-mappings.service
   ```

---

## **How It Works**

1. **Retrieve PCI Device Information**:
    - The script uses `lspci -vmm` to extract detailed information about all PCI devices.
    - Each device's details (e.g., slot, device name) are parsed into a structured format.

2. **Update Configuration File**:
    - The script reads the existing `/etc/pve/mapping/pci.cfg` file using Python's `configparser`.
    - For each detected PCI device, it updates or creates entries with dynamically retrieved parameters:
      - `id`: Based on the PCI slot (e.g., `00:1f.2` becomes `00_1f_2`).
      - `iommugroup`: Placeholder (can be extended to retrieve actual IOMMU group data).
      - `node`: Hostname of the current node.
      - `path`: Path to the PCI device in `/sys/bus/pci/devices`.
      - `subsystem-id`: Subsystem identifier (device name).

3. **Write Back Changes**:
    - The updated configuration is written back to `/etc/pve/mapping/pci.cfg`, overwriting its previous content.

4. **Automated Execution**:
    - The systemd service ensures that the script runs automatically during boot, keeping PCI mappings up-to-date.

---

## **Verification**

After installation, verify that `/etc/pve/mapping/pci.cfg` has been updated with accurate mappings by inspecting its contents:

```bash
cat /etc/pve/mapping/pci.cfg
```

Example output:
```
[00_1f_2]
id=00_1f_2
iommugroup=unknown
node=my-proxmox-node
path=/sys/bus/pci/devices/0000:00:1f.2
subsystem-id=Intel Corporation 82801JI (ICH10 Family) SATA Controller [AHCI mode]
```

---

## **Extending Functionality**
- Replace placeholders like `iommugroup` with logic to dynamically retrieve actual IOMMU group data from `/sys/kernel/iommu_groups`.
- Add error handling for edge cases, such as missing devices or inaccessible files.
- Customize parameters based on specific use cases or hardware requirements.

---

## **License**
This project is open-source and can be freely modified or distributed under an appropriate license.

---

## **Contributions**
Feel free to submit issues or pull requests to improve functionality or compatibility with other environments!