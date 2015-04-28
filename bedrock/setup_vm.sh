#! /usr/bin/env bash

# This script is used to setup Bedrock on a clean virtual machine with
# Debian 8 64bit. Packages selected during install: SSH server, Standard
# System Utilities.
# It clones a forked repository and set the original repository as remote

# Before starting you need to install sudo and add your user to the sudoers
# group.
# (as root) apt-get install sudo; adduser $username sudo

forked_user=flodolo
original_user=mozilla
install_folder=/home/flodolo/github

# Update the system
sudo apt-get update
sudo apt-get upgrade -y --show-upgraded

# Install necessary packages and enable modrewrite
sudo apt-get install -y build-essential curl git libmysqlclient-dev libxml2-dev libxslt1-dev python-dev subversion zlib1g-dev

# Install node
curl -sL https://deb.nodesource.com/setup_0.12 | sudo bash -
sudo apt-get install -y nodejs

# Install pip, virtualenv
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
sudo pip install virtualenv

# Don't generate .pyc files
echo "PYTHONDONTWRITEBYTECODE=1" >> ~/.bashrc

# Clone forked repository and set original repository as remote
mkdir -p $install_folder
cd $install_folder
git clone --recursive https://github.com/$forked_user/bedrock
cd bedrock
git remote add upstream https://github.com/$original_user/bedrock
git fetch upstream
git merge upstream/master

virtualenv venv
source venv/bin/activate
bin/peep.py install -r requirements/dev.txt
bin/peep.py install -r requirements/prod.txt

# Setup up config file with settings useful for l10n
# Common alternative: cp bedrock/settings/local.py-dist bedrock/settings/local.py
echo "
ADMINS = ('nobody@locahost',)
MANAGERS = ADMINS

DEBUG = TEMPLATE_DEBUG = True
#DEV = False
DEV = True
DOTLANG_CACHE = 0

# Google Apps tracking code
GA_ACCOUNT_CODE = ''

SESSION_COOKIE_SECURE = False

HMAC_KEYS = {
    '2011-01-01': 'cheesecake',
}
" > bedrock/settings/local.py

# Sync product-details and other things
bin/sync_all

# Clone locales
svn co https://svn.mozilla.org/projects/mozilla.com/trunk/locales/ locale

# Run server to check if there are errors
./manage.py runserver 0.0.0.0:8000
