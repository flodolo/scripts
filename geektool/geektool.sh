#! /usr/bin/env bash

printf "IP:      `ifconfig en0 | grep inet | grep -v inet6 | awk '{print $2}'`\n"
printf "Gateway: `route -n get default | grep gateway | awk '{print $2}'`\n"
