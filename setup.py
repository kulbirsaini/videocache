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
import pwd
import sys
import traceback

if __name__ == '__main__':
    # Parse command line options.
    parser = OptionParser()
    parser.add_option('-v', '--verbose', dest = 'verbose', action='store_true', help = 'Print detailed log messages.', default = False)
    parser.add_option('-p', '--prefix', dest = 'vc_root', type='string', help = 'Specify an alternate root location for videocache', default = '/')
    parser.add_option('-u', '--squid-user', dest = 'squid_user', type='string', help = 'User who runs Squid daemon.')
    parser.add_option('-a', '--apache-dir', dest = 'apache_dir', type='string', help = 'Path to conf.d directory for Apache. In most cases, it\'ll be /etc/httpd/conf.d/ or /etc/apache2/conf.d/.')
    parser.add_option('-s', '--skip-apache-conf', dest = 'skip_apache_conf', action='store_true', help = 'Skip creating Videocache specific configuration for Apache.', default = False)
    options, args = parser.parse_args()

    help_message =  """
Usage: python setup.py install (as root/super user)
Please see http://cachevideos.com/installation for more information or getting help.
"""

    uid_error = """
You must be root to setup/install videocache.
Please see http://cachevideos.com/installation for more information or getting help.
"""

    if os.getuid() != 0:
        parser.print_help()
        sys.stderr.write(uid_error)
        sys.exit(1)

    if 'install' not in args:
        parser.print_help()
        sys.stderr.write(help_message)
        sys.exit(1)

    if options.squid_user == None or options.squid_user == '':
        try:
            pwd.getpwnam('proxy')
            options.squid_user = 'proxy'
        except Exception, e:
            pass

        try:
            pwd.getpwnam('squid')
            options.squid_user = 'squid'
        except Exception, e:
            pass
        if options.squid_user == None or options.squid_user == '':
            parser.print_help()
            sys.stderr.write('\nPlease use -u (or --squid-user) option to specify the user who runs Squid daemon.\n')
            sys.exit(1)

    if options.skip_apache_conf:
        apache_dir = None
    elif options.apache_dir == None or options.apache_dir == '':
        httpd_dir = os.path.join(options.vc_root, 'etc/httpd/conf.d/')
        apache2_dir = os.path.join(options.vc_root, 'etc/apache2/conf.d/')
        apache1_dir = os.path.join(options.vc_root, 'etc/apache/conf.d/')
        if os.path.isdir(httpd_dir):
            apache_dir = httpd_dir
        elif os.path.isdir(apache2_dir):
            apache_dir = apache2_dir
        elif os.path.isdir(apache1_dir):
            apache_dir = apache1_dir
        else:
            parser.print_help()
            sys.stderr.write('\nPlease use -a (or --apache-dir) option to specify the path to Apache\'s conf.d directory.\n')
            sys.exit(1)
    else:
        apache_dir = options.apache_dir

    if options.vc_root[0] != '/':
        root = os.path.join(os.getcwd(), options.vc_root)
    else:
        root = options.vc_root

    working_dir = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))
    # The location of system configuration file for videocache.
    videocache_dir = os.path.join(working_dir, 'videocache')
    config_file = os.path.join(working_dir, 'videocache-sysconfig.conf')
    man_page = os.path.join(working_dir, 'videocache.8.gz')

    if os.path.isdir(videocache_dir):
        sys.path = [videocache_dir] + sys.path
        from vcoptions import VideocacheOptions
        from common import *
    else:
        sys.stderr.write(help_message)
        parser.print_help()
        sys.exit(1)

    try:
        o = VideocacheOptions(config_file)
    except Exception, e:
        parser.print_help()
        log_traceback()
        sys.stderr.write('\nvc-setup: Could not read options from configuration file.\n')
        sys.exit(1)

    if o.halt:
        parser.print_help()
        sys.stderr.write('\nvc-setup: One or more errors occured in reading configure file. Please check syslog messages generally located at /var/log/messages.\n')
        sys.exit(1)

    setup_vc(o, root, options.squid_user, apache_dir, working_dir, not options.verbose)

