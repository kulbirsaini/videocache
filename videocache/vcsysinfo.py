#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import platform
import re
import subprocess

def get_dist_details():
    try:
        dist = platform.dist('Unknown', 'Unknown', 'Unknown')
        return { 'os_name' : dist[0], 'os_version' : dist[1], 'os_id' : dist[2] }
    except Exception, e:
        return { 'os_name' : 'Unknown', 'os_version' : 'Unknown', 'os_id' : 'Unknown' }

def get_python_version():
    try:
        return { 'python_version' : platform.python_version() }
    except Exception, e:
        return { 'python_version' : 'Unknown' }

def get_system_name():
    try:
        return { 'system' : platform.system() }
    except Exception, e:
        return { 'system' : 'Unknown' }

def get_system_arch():
    try:
        return { 'architecture' : platform.machine() }
    except Exception, e:
        return { 'architecture' : 'Unknown' }

def is_valid_ip(ip):
    if ip.startswith('127') or ip.startswith('255') or ip.endswith('255') or ip.endswith('0'):
        return False
    else:
        return True

def get_ip_addresses():
    try:
        co = subprocess.Popen(['ifconfig'], stdout = subprocess.PIPE)
        ifconfig = co.stdout.read()
        ip_regex = re.compile('((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-4]|2[0-5][0-9]|[01]?[0-9][0-9]?))')
        addresses = [match[0] for match in ip_regex.findall(ifconfig, re.MULTILINE)]
        ips = []
        for address in addresses:
            if is_valid_ip(address):
                ips.append(address)
        return { 'ip_addresses' : ', '.join(ips) }
    except Exception, e:
        return { 'ip_addresses' : '' }

def get_all_info():
    info = {}
    info.update(get_dist_details())
    info.update(get_python_version())
    info.update(get_system_name())
    info.update(get_system_arch())
    info.update(get_ip_addresses())
    return info

