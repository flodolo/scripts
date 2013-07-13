#! /usr/bin/env bash

# This script is used to setup Transvision on a clean virtual machine with
# Debian 7 64bit. Packages selected during install: SSH server, Standard
# System Utilities.
# It clones a forked repository and set the original repository as remote,
# then change Transvision as the default website.

# Before starting you need to install sudo and add your user to the sudoers
# group.
# (as root) apt-get install sudo; adduser $username sudo

forkedrepo=https://github.com/flodolo/transvision
originalrepo=https://github.com/mozfr/transvision
branch=master

# Update the system
sudo apt-get update
sudo apt-get upgrade -y --show-upgraded
sudo echo "transvision" > /etc/hostname

# Install necessary packages and enable modrewrite
sudo apt-get install -y git subversion mercurial apache2 php5 curl
sudo a2enmod rewrite

# Clone forked repository and set original repository as remote
mkdir ~/github
cd ~/github
git clone $forkedrepo
cd ~/github/transvision
git remote add upstream $originalrepo
git fetch upstream
git merge upstream/master
git checkout $branch

# Set config.ini

homefolder=$(readlink -f ~)

echo "[config]
root=$homefolder/transvision
local_hg=$homefolder/transvision/data/hg
libraries=$homefolder/transvision/libraries
install=$homefolder/github/transvision
" > ~/github/transvision/web/inc/config.ini

# Run Transvision setup
./setup.sh

# Set default Transvision as the default webserver and change AllowOverride
# directive (None->All). This obviously makes sense only on a dedicated VM
sudo cp /etc/apache2/sites-available/default /etc/apache2/sites-available/default_old
sudo sed -i "s|/var/www|$homefolder/github/transvision/web|g" /etc/apache2/sites-available/default
sudo sed -i "s|AllowOverride None|AllowOverride All|g" /etc/apache2/sites-available/default
sudo /etc/init.d/apache2 restart

# Install composer
cd ~/github/transvision/web
curl -sS https://getcomposer.org/installer | php
php composer.phar install