UBUNTU_VERSION="Ubuntu 20.04.5 LTS"
MPTCP_VERSION="5.4.230.mptcp"

# Check if correct version of Ubuntu is used
if ! lsb_release -d | grep -q "$UBUNTU_VERSION"; then
	echo "Please install $UBUNTU_VERSION to continue!"
	exit 0
fi

if [[ $UID != 0 ]]; then
	echo "Please run this script with sudo:"
	echo "sudo $0 $*"
	exit 1
fi

# Install dependencies
sudo apt-get -y install python3 mininet python3-pip

# Install Python3 dependencies
sudo pip3 install matplotlib mininet

# Create temp folder
TEMP_FOLDER="temp"
sudo rm -rf $TEMP_FOLDER
mkdir $TEMP_FOLDER

# Download mptcp kernel files
wget -P $TEMP_FOLDER https://github.com/multipath-tcp/mptcp/releases/download/v0.96/linux-headers-5.4.230.mptcp_20230203134326-1_amd64.deb
wget -P $TEMP_FOLDER https://github.com/multipath-tcp/mptcp/releases/download/v0.96/linux-image-5.4.230.mptcp_20230203134326-1_amd64.deb
wget -P $TEMP_FOLDER https://github.com/multipath-tcp/mptcp/releases/download/v0.96/linux-libc-dev_20230203134326-1_amd64.deb
wget -P $TEMP_FOLDER https://github.com/multipath-tcp/mptcp/releases/download/v0.96/linux-mptcp_v0.96_20230203134326-1_all.deb

# Install mptcp kernel
sudo dpkg -i temp/linux*.deb
sudo apt-get install -f

# Clean up
sudo rm -rf $TEMP_FOLDER

# Make it so that grub default boots latest chosen kernel
GRUB_PARAMETER="GRUB_SAVEDEFAULT=true"
GRUB_PATH="/etc/default/grub"
if ! grep -q "^$GRUB_PARAMETER" "$GRUB_PATH"; then
	echo "$GRUB_PARAMETER" >> $GRUB_PATH
fi
sudo sed -i "s/GRUB_DEFAULT=.*/GRUB_DEFAULT=saved/g" $GRUB_PATH

# Update grub
sudo update-grub

echo ""
echo "Installation process is complete!"
echo "Please select the $MPTCP_VERSION under advanced options during next boot to set it as default!"

read -r -p "Would you like to reboot now? [Y/n]: " response
response=${response,,} # tolower
if [[ $response =~ ^(y| ) ]] || [[ -z $response ]]; then
	reboot
fi
