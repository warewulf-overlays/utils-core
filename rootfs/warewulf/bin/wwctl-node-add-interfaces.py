#!/usr/bin/env python3

# Author: griznog
# Purpose: Present all local network interfaces as wwctl command to add them to the node config.

import subprocess
import json
import socket
import re

# How to match an IB interface. Thie will break in Rocky 9 as IB interface names start getting
# bus info added to them. 
re_infiniband = re.compile('^ib[0-9]+')
# After figuring this out I realized I can just slice the string, but leaving this here 
# for posterity because it's awesome. 
re_infiniband_split_hwaddr = re.compile("((?:[0-9a-fA-F]{2}:?){12}):((?:[0-9a-fA-F]{2}:?){8})")

# Who am I?
hostname = socket.gethostname()

# IP Addresses.
status, output = subprocess.getstatusoutput('ip -4 -j addr')
ip_addr_info = json.loads(output)

# Hardware Info
status, output = subprocess.getstatusoutput('ip -j link')
ip_link_info = json.loads(output)

# Interface Info
if_info = {}

for interface in ip_addr_info:
    if_info[interface['ifname']] = { 'ipaddr' : [ sub['local'] for sub in interface['addr_info'] ] }

for interface in ip_link_info:
    try:
        if_info[interface['ifname']]['hwaddr'] = interface['address']
    except KeyError:
        if_info[interface['ifname']] = { 'hwaddr' : interface['address'] }


for interface in if_info.keys():
    if interface == 'lo':
        continue
   
    # Clear up stuff for this iteration.
    nettags=[]

    # Pull out the hwaddr, we'll need to carve it up for IB
    hwaddr = if_info[interface]['hwaddr']

    m = re_infiniband.match(interface)
    if m:
        # We have an IB interface, need to calculate WW friendly hwaddr and tags.
        ib_hwaddr = hwaddr
        ib_portguid = ib_hwaddr[36:]
        ib_clientid = "ff:00:00:00:00:00:02:00:00:02:c9:00:%s" % ib_portguid
        # We use the 48 bit hwaddr as teh WW HWADDR.
        hwaddr = ib_portguid[:9] + ib_portguid[15:]
        
        nettags = [ 'ibhwaddr=%s' % ib_hwaddr, 'ibportguid=%s' % ib_portguid, 'ibclientid=%s' % ib_clientid]

    
    ipaddr_flag = ''
    try:
        # Blindly take the first IP address, WW only has space for 1. 
        ipaddr_flag = "--ipaddr=%s" %  if_info[interface]['ipaddr'][0]
    except KeyError:
        pass

    # Set up flags.
    hwaddr_flag = "--hwaddr=%s" % hwaddr
    nettag_flag = " ".join([ '--nettag="%s"' % tag for tag in nettags ])
    print("wwctl node set --netname=%s --netdev=%s %s %s %s %s" % (interface, interface, hwaddr_flag, ipaddr_flag, nettag_flag, hostname))

