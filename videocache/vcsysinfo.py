#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import os
import platform
import re
import subprocess

def get_dist_details():
    try:
        dist = platform.dist('Unknown', 'Unknown', 'Unknown')
        if dist[0] == 'Unknown':
            dist[0] = platform.system()
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
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    if parts[0] == '127' or parts[0] == '169' or parts[0] == '0' or int(parts[0]) > 223:
        return False
    if parts[3] == '0' or parts[3] == '255':
        return False
    return True

def is_valid_mac(mac):
    if mac == '00:00:00:00:00:00' or mac.lower() == 'ff:ff:ff:ff:ff:ff':
        return False
    return True

def get_interface_details():
    try:
        import netifaces
        macs = []
        ips = []
        for iface in netifaces.interfaces():
            if iface == 'lo' or iface.startswith('vbox'):
                continue
            iface_details = netifaces.ifaddresses(iface)
            if iface_details.has_key(netifaces.AF_INET):
                ipv4 = iface_details[netifaces.AF_INET]
                ips.extend(map(lambda x: x['addr'], filter(lambda x: x.has_key('addr') and is_valid_ip(x['addr']), ipv4)))

            if iface_details.has_key(netifaces.AF_LINK):
                link = iface_details[netifaces.AF_LINK]
                macs.extend(map(lambda x: x['addr'], filter(lambda x: x.has_key('addr') and is_valid_mac(x['addr']), link)))

        return { 'ip_addresses' : ', '.join(ips), 'mac_addresses' : ', '.join(macs) }
    except Exception, e:
        return { 'ip_addresses' : get_ip_addresses(), 'mac_addresses' : get_mac_addresses() }

def get_ip_addresses():
    cmd = "ifconfig | grep inet | grep -v inet6 | awk '{print $2}' | cut -d\: -f2 | cut -d\  -f1 "

    for path in ['/sbin/', '', '/bin/']:
        command = os.path.join(path, cmd)
        try:
            co = subprocess.Popen([command], shell = True, stdout = subprocess.PIPE)
            ifconfig = co.stdout.read().strip()
            if co.poll() is None:
                co.terminate()
            ips = ', '.join(filter(lambda x: is_valid_ip(x.strip()), ifconfig.split("\n")))
            if ips != '':
                return ips
        except Exception, e:
            continue
    return ''

def get_mac_addresses():
    cmd = 'ifconfig'
    mac_regex = re.compile('(hwaddr|ether).*(([0-9A-F]{2}:){5}[0-9A-F]{2})', re.I)
    for path in ['/sbin/', '', '/bin/']:
        command = os.path.join(path, cmd)
        try:
            co = subprocess.Popen([command], stdout = subprocess.PIPE, env = { 'LC_ALL' : 'C' })
            ifconfig = co.stdout.read()
            if co.poll() is None:
                co.terminate()
            macs = ', '.join(filter(lambda x: is_valid_mac(x), [i[1] for i in mac_regex.findall(ifconfig, re.MULTILINE)]))
            if macs != '':
                return macs
        except Exception, e:
            pass

    return ''

def get_all_info(o):
    info = {}
    info.update(get_dist_details())
    info.update(get_python_version())
    info.update(get_system_name())
    info.update(get_system_arch())
    info.update(get_interface_details())
    return info

