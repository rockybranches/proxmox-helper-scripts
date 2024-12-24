#!/bin/bash

# Run this script from the root repo directory

set -e

SCRIPT_LOC='/usr/local/bin/update_pci_mappings.py'
echo -e "Copying script to '$SCRIPT_LOC' ..."
# copy to intended script loc
sudo cp ./scripts/update_pci_mappings/update_pci_mappings.py $SCRIPT_LOC
# add executable permissions
sudo chmod +x $SCRIPT_LOC

# create systemd service
SERVICE_LOC='/etc/systemd/system/update-pci-mappings.service'
echo -e "Creating systemd service '$SERVICE_LOC' ..."
cat <<EOF > "$SERVICE_LOC"
[Unit]
Description=Update PCI Mappings for Proxmox VE
After=network.target local-fs.target
Requires=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /usr/local/bin/update_pci_mappings.py

[Install]
WantedBy=multi-user.target
EOF

# setup systemd service
sudo systemctl enable update-pci-mappings.service
sudo systemctl start update-pci-mappings.service
sleep 1s
systemctl status update-pci-mappings.service

# note: verify service execution on boot:
# '$ journalctl -u update-pci-mappings.service'
