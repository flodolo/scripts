#! /usr/bin/env bash

# Restart network stuck on Debian VM
sudo ifconfig eth0 up
sudo /etc/init.d/networking restart