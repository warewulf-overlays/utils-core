#!/bin/bash

# Author: griznog
# Purpose: Quick hack to make it easy to clone a disk partition layout.

# Pull in warewulf functions/variables for this node.
[[ -f /warewulf/etc/functions ]] && source /warewulf/etc/functions || exit 1

# Script starts here
# Verify we are actually being given a real disk as arg 1.
if ! [[ $1 =~ /dev/(sd[a-z]*|nvme[0-9]*n1)$ ]]; then
    echo "I can't handle $1"
    exit 1
fi

if [[ ! -b $1 ]]; then
    echo "$1 not a block device."
    exit 2
fi

# Verify that $2 at least looks like a disk. 
if ! [[ $2 =~ /dev/(sd[a-z]*|nvme[0-9]*n1)$ ]]; then
    echo "I can't handle $2"
    exit 1
fi

# Build the clone command and display it.
echo -n "sgdisk -o "
sgdisk -p $1 | awk '/^   [1-9]/ {print "-n " $1 ":" $2 ":" $3 " -t " $1 ":" $6 }' | tr '\n' ' '
echo $2 

