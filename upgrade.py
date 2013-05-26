#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from optparse import OptionParser

import os
import sys
import traceback

def red(msg):
    return "\033[1;31m%s\033[0m" % msg

def blue(msg):
    return "\033[1;36m%s\033[0m" % msg

def green(msg):
    return "\033[1;32m%s\033[0m" % msg

def print_message_and_abort(message):
    print >>sys.stderr, message
    sys.exit(1)

def log_traceback():
    print blue('\n' + '-' * 25 + 'Traceback Begin' + '-' * 25)
    print traceback.format_exc(),
    print blue('-' * 25 + 'Traceback End' + '-' * 27 + '\n')

# Setup specific functions
def setup_error(error_code):
    """Report error while updating/installing videocache with proper error code."""

    messages = {}
    messages['usage'] =  """
Usage: python upgrade.py [options]

$ python upgrade.py -h

Usage: python upgrade.py
"""

    messages['upgrade'] =  """An error has occured while upgrading videocache.
Please fix the error and try upgrading again.

Please see http://cachevideos.com/#install for more information or getting help."""

    messages['uid'] = """
You must run Videocache installer as root or with sudo.
Please see http://cachevideos.com/#install for more information or getting help.
"""
    if error_code in messages:
        return messages[error_code]
    return ''

def upgrade_vc(o, quiet):
    """Perform the setup."""
    install_dir = '/usr/share/videocache/'
    etc_dir = '/etc/'
    usr_sbin_dir = '/usr/sbin/'
    init_dir = '/etc/init.d/'

    upgrade_error = blue("\n\n" + setup_error('upgrade'))

    dirs_to_be_created = [install_dir, etc_dir, usr_sbin_dir, init_dir]

    if not o.skip_apache_conf:
        dirs_to_be_created += [o.apache_conf_dir]

    for dir in dirs_to_be_created:
        if not create_or_update_dir(dir, None, 0755, quiet):
            print_message_and_abort(red("Could not create directory %s" % dir) + upgrade_error)

    for dir in sum([o.base_dir_list] + [[o.logdir]] + [v for (k, v) in o.base_dirs.items()], []):
        if not create_or_update_dir(dir, o.videocache_user, 0755, quiet):
            print_message_and_abort(red("Could not create directory %s" % dir) + upgrade_error)

    # Copy core videocache plugin code to /usr/share/videocache/ .
    if not copy_dir(os.path.join(working_dir, 'videocache'), install_dir, quiet):
        print_message_and_abort(red("Could not copy Videocache to installation directory %s" % install_dir) + upgrade_error)

    if not set_permissions_and_ownership(install_dir, o.videocache_user, 0755, quiet):
        print_message_and_abort(red("Could not set ownership and permissions for installation directory %s" % install_dir) + upgrade_error)

    for filename in os.listdir(install_dir):
        filepath = os.path.join(install_dir, filename)
        if not set_permissions_and_ownership(filepath, o.videocache_user, 0755, quiet):
            print_message_and_abort(red("Could not set ownership and permissions for file %s" % filepath) + upgrade_error)

    # Copy vc-scheduler.rc to /etc/init.d/
    if not copy_file(os.path.join(working_dir, 'vc-scheduler.rc'), os.path.join(init_dir, 'vc-scheduler'), quiet):
        print_message_and_abort(red("Could not copy Videocache scheduler init file to %s" % os.path.join(init_dir, 'vc-scheduler')) + upgrade_error)

    # Generate Apache webserver configuration file for videocache.
    if o.apache_conf_dir and not generate_httpd_conf(os.path.join(o.apache_conf_dir, 'videocache.conf'), o.base_dir_list, o.cache_host, True, quiet):
        print_message_and_abort(red("Could not generate Apache specific configuration file at %s" % os.path.join(o.apache_conf_dir, 'videocache.conf')) + upgrade_error)

    # Create tables for filelist database
    try:
        initialize_database(o)
        if not create_tables():
            print_message_and_abort(red("Could not create database tables for filelist db"))
    except Exception, e:
        log_traceback()
        print_message_and_abort(upgrade_error)

    try:
        src_vc_update = os.path.join(install_dir, 'vc-update')
        src_vc_scheduler = os.path.join(install_dir, 'vc-scheduler')
        dst_vc_update = os.path.join(usr_sbin_dir, 'vc-update')
        dst_vc_cleaner = os.path.join(usr_sbin_dir, 'vc-cleaner')
        dst_vc_scheduler = os.path.join(usr_sbin_dir, 'vc-scheduler')
        dst_vc_cleaner_cron = os.path.join('/etc/cron.daily/', 'vc-cleaner')

        if os.path.islink(dst_vc_update) or os.path.isfile(dst_vc_update): os.unlink(dst_vc_update)
        if os.path.islink(dst_vc_cleaner) or os.path.isfile(dst_vc_cleaner): os.unlink(dst_vc_cleaner)
        if os.path.islink(dst_vc_scheduler) or os.path.isfile(dst_vc_scheduler): os.unlink(dst_vc_scheduler)
        if os.path.islink(dst_vc_cleaner_cron) or os.path.isfile(dst_vc_cleaner_cron): os.unlink(dst_vc_cleaner_cron)

        os.symlink(src_vc_update, dst_vc_update)
        os.symlink(src_vc_scheduler, dst_vc_scheduler)
    except Exception, e:
        log_traceback()
        print_message_and_abort(upgrade_error)

    squid_config_lines = "access_log %s\nacl this_machine src 127.0.0.1 %s \nhttp_access allow this_machine" % (o.squid_access_log, get_ip_addresses().replace(',', ' '))

    print green("Videocache upgraded successfully. Please follow the following instructions now.\n")
    print blue("----------------------------------Step 1-----------------------------------------")
    print red("Restart Apache web server on your machine by using the following command")
    print red("[root@localhost ~]# apachectl -k restart")
    print
    print blue("----------------------------------Step 2-----------------------------------------")
    print red("Depending on the version of your Squid, open vc_squid_2.conf or vc_squid_3.conf")
    print red("in your Videocache bundle. Copy all the lines and paste them at the top of your")
    print red("Squid configuration file squid.conf. Remove the old videocache specific lines first.")
    print
    print green("Also, add the following lines at the top of your Squid config file squid.conf.")
    print blue("#-----------------CUT FROM HERE-------------------")
    print blue("%s" % squid_config_lines)
    print blue("#-----------------CUT TILL HERE-------------------")
    print
    print blue("----------------------------------Step 3-----------------------------------------")
    print red("Restart videocache scheduler vc-scheduler using the following command.")
    print red("[root@localhost ~]# vc-scheduler -s restart")
    print
    print blue("----------------------------------Step 4-----------------------------------------")
    print red("Restart Squid proxy server daemon using the following command.")
    print red("[root@localhost ~]# /etc/init.d/squid restart")
    print
    print blue("----------------------------------Step 5-----------------------------------------")
    print red("Go the videocache log directory /var/log/videocache/ and check various log files")
    print red("to have a look at videocache activity.")
    print
    print
    print green("Check Manual.pdf file for detailed configurations of squid, apache and videocache.")
    print green("In case of any bugs or problems, visit http://cachevideos.com/ and contact us.")
    return

if __name__ == '__main__':
    # Parse command line options.
    parser = OptionParser()
    parser.add_option('-v', '--verbose', dest = 'verbose', action='store_true', help = 'Print detailed log messages.', default = False)
    options, args = parser.parse_args()

    working_dir = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))
    videocache_dir = os.path.join(working_dir, 'videocache')
    config_file = '/etc/videocache.conf'

    if not os.path.isfile(config_file):
        print_message_and_abort(red("\nCound not locate Videocache config file at " + config_file + ".\nLooks like you don't have Videocache installed.\nPlease try to use installer script install.sh to install Videocache."))

    if os.path.isdir(videocache_dir):
        try:
            sys.path = [videocache_dir] + sys.path
            from vcoptions import VideocacheOptions
            from common import *
            from fsop import *
            from vcsysinfo import get_ip_addresses
            from database import create_tables, initialize_database
        except Exception, e:
            log_traceback()
            print_message_and_abort(red("\nCould not import required modules for upgrade.") + green("\nIf you contact us regarding this error, please send the Trace above."))
    else:
        print_message_and_abort(red("Could not locate the videocache directory in bundle.\n%s" % setup_error('usage')))

    try:
        o = VideocacheOptions(config_file, True, True)
    except Exception, e:
        log_traceback()
        print_message_and_abort(red("\nCould not read options from configuration file located at %s ." % config_file) + green("\nIf you contact us regarding this error, please send the Trace above."))

    if o.halt:
        print_message_and_abort(red('\nOne or more errors occured in reading configuration file.\nPlease check syslog messages generally located at /var/log/messages or /var/log/syslog.') + green("\nIf you contact us regarding this error, please send the log messages."))


    try:
        filedesc = open(config_file, 'r')
        config_data = filedesc.read()
        filedesc.close()
        filedesc = open(config_file, 'w')
        config_data = re.sub(r"\n#\s+version\s+:\s+([0-9\.])+\s+revision\s+([^ \n]+)\n", r"\n# version : %s revision %s\n" % (o.version, o.revision), config_data, count = 0)
        filedesc.write(config_data)
        filedesc.close()
    except Exception, e:
        pass #FIXME

    upgrade_vc(o, not options.verbose)

