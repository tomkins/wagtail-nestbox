#! /usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Get a GitHub access token to use API
read -r -p "Enter GitHub personal access token: " GITHUB_TOKEN
rm -f /etc/nestbox_env.conf
touch /etc/nestbox_env.conf
chmod 600 /etc/nestbox_env.conf
echo "GITHUB_TOKEN=$GITHUB_TOKEN" >> /etc/nestbox_env.conf

# Install all needed dependencies
apt update
apt -y dist-upgrade
apt install -y git python3-dev fonts-wqy-microhei

# Enable SPI
sed -i -e 's|^#dtparam=spi=on$|dtparam=spi=on|g' /boot/firmware/config.txt

# Clone/setup code
adduser --system nestbox
mkdir -p /usr/local/lib/nestbox/{venv,code}
chown -R nestbox:nogroup /usr/local/lib/nestbox
sudo -u nestbox git clone https://github.com/tomkins/wagtail-nestbox.git /usr/local/lib/nestbox/code
sudo -u nestbox python3 -m venv /usr/local/lib/nestbox/venv
sudo -u nestbox /usr/local/lib/nestbox/venv/bin/python -m pip install --no-cache-dir -r /usr/local/lib/nestbox/code/requirements.txt

# Setup systemd service
cp -a /usr/local/lib/nestbox/code/nestbox.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable nestbox.service

# Reboot!
shutdown -r now
