#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from optparse import OptionParser

import os
import sys

if __name__ == '__main__':
    # Parse command line options.
    parser = OptionParser()
    parser.add_option('-p', '--prefix', dest = 'vc_root', type='string', help = 'Specify an alternate root location for videocache', default = '/')
    parser.add_option('-a', '--apache-dir', dest = 'apache_dir', type='string', help = 'Path to conf.d directory for Apache. Default is /etc/httpd/conf.d/', default = '/etc/httpd/conf.d/')
    options, args = parser.parse_args()

    working_dir = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))
    # The location of system configuration file for videocache.
    videocache_dir = os.path.join(working_dir, 'videocache')
    config_file = os.path.join(working_dir, 'videocache-sysconfig.conf')
    apache_config_file = os.path.join(working_dir, 'videocache-httpd.conf')
    man_page = os.path.join(working_dir, 'videocache.8.gz')

    if os.path.isdir(videocache_dir):
        sys.path = [videocache_dir] + sys.path
        from vcoptions import VideocacheOptions
        from common import *
    else:
        help_message =  """
Usage: python setup.py install (as root/super user)
Please see http://cachevideos.com/installation for more information or getting help.
        """
        sys.stderr.write(help_message)

    if 'install' not in args:
        setup_error('usage')

    if os.getuid() != 0:
        setup_error('uid')

    try:
        o = VideocacheOptions(config_file)
    except Exception, e:
        message = 'vc-setup: Could not read options from configuration file.'
        sys.stderr.write(message)
        sys.exit(1)

    if o.halt:
        message = 'vc-setup: One or more errors occured in reading configure file. Please check syslog messages generally located at /var/log/messages.'
        sys.stderr.write(message)
        sys.exit(1)

    setup_vc(o, options.vc_root, options.apache_dir, working_dir)

