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
import pwd
import sys
import traceback

# Setup specific functions
def print_message_and_abort(message):
    sys.stderr.write(message)
    sys.exit(1)

def setup_error(error_code):
    """Report error while updating/installing videocache with proper error code."""

    usage =  """
Usage: python setup.py install (as root/super user)
Please see http://cachevideos.com/#install for more information or getting help.
"""
    install_error =  """
An error has occured while installing videocache.
Please see http://cachevideos.com/#install for more information or getting help.
"""
    uid_error = """
You must be root to setup/install videocache.
Please see http://cachevideos.com/#install for more information or getting help.
"""
    messages = { 'usage' : usage, 'uid' : uid_error, 'install' : install_error }
    if messages.has_key(error_code): print_message_and_abort(messages[error_code])
    return

def setup_success():
    """Print informative messages after successfull installation."""
    message = """
Videocache setup has completed successfully.
Now you must restart Apache web server on your machine by using the following command
[root@localhost ~]# apachectl -k restart [ENTER]

Also, you need to configure squid so that it can use videocache as a url rewriter plugin.
Check README file for further configurations of squid, apache and videocache.
In case of any bugs or problems, check http://cachevideos.com/ .
    """
    print message

def setup_vc(o, root, squid_user, apache_conf_dir, working_dir, quiet, skip_config):
    """Perform the setup."""
    install_dir = apply_install_root(root, '/usr/share/videocache/')
    etc_dir = apply_install_root(root, '/etc/')
    usr_sbin_dir = apply_install_root(root, '/usr/sbin/')
    var_dir = os.path.dirname(o.scheduler_pidfile)
    man_dir = apply_install_root(root, '/usr/share/man/man8/')
    cron_dir = apply_install_root(root, '/etc/cron.daily/')
    init_dir = apply_install_root(root, '/etc/init.d/')

    if apache_conf_dir:
        apache_conf_dir = apply_install_root(root, apache_conf_dir)
        if not create_or_update_dir(apache_conf_dir, None, 0755, quiet):
            setup_error('update')

    for dir in [install_dir, etc_dir, usr_sbin_dir, var_dir, man_dir, cron_dir, init_dir]:
        if not create_or_update_dir(dir, None, 0755, quiet): setup_error('update')

    for dir in sum([o.base_dir_list] + [[o.logdir]] + [v for (k, v) in o.base_dirs.items()], []):
        if not create_or_update_dir(dir, squid_user, 0755, quiet): setup_error('update')

    # Copy core videocache plugin code to /usr/share/videocache/ .
    if not copy_dir(os.path.join(working_dir, 'videocache'), install_dir, quiet): setup_error('install')

    if not set_permissions_and_ownership(install_dir, squid_user, 0755, quiet): setup_error('install')

    for filename in os.listdir(install_dir):
        if not set_permissions_and_ownership(os.path.join(install_dir, filename), squid_user, 0755, quiet): setup_error('install')

    # Copy videocache-sysconfig.conf to /etc/videocache.conf .
    if not skip_config:
        vcsysconfig_file = os.path.join(etc_dir, 'videocache.conf')
        if not copy_file(os.path.join(working_dir, 'videocache-sysconfig.conf'), vcsysconfig_file, quiet): setup_error('install')

        file = open(vcsysconfig_file, 'r')
        config_data = file.read()
        file.close()
        file = open(vcsysconfig_file, 'w')
        file.write(config_data.replace('videocache_user = squid', 'videocache_user = ' + squid_user))
        file.close()

    # Copy vc-scheduler.rc to /etc/init.d/
    if not copy_file(os.path.join(working_dir, 'vc-scheduler.rc'), os.path.join(init_dir, 'vc-scheduler'), quiet): setup_error('install')

    # Copy videocache.8.gz (manpage) to /usr/share/man/man8/videocache.8.gz
    if not copy_file(os.path.join(working_dir, 'videocache.8.gz'), os.path.join(man_dir, 'videocache.8.gz'), quiet): setup_error('install')

    # Generate Apache webserver configuration file for videocache.
    if apache_conf_dir and not generate_httpd_conf(os.path.join(apache_conf_dir, 'videocache.conf'), o.base_dir_list, quiet): setup_error('install')

    try:
        src_vc_update = os.path.join(install_dir, 'vc-update')
        src_vc_cleaner = os.path.join(install_dir, 'vc-cleaner')
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
        os.symlink(src_vc_cleaner, dst_vc_cleaner)
        os.symlink(src_vc_scheduler, dst_vc_scheduler)
        os.symlink(src_vc_cleaner, dst_vc_cleaner_cron)
    except Exception, e:
        log_traceback()
        setup_error('install')

    setup_success()
    return

if __name__ == '__main__':
    # Parse command line options.
    parser = OptionParser()
    parser.add_option('-v', '--verbose', dest = 'verbose', action='store_true', help = 'Print detailed log messages.', default = False)
    parser.add_option('-p', '--prefix', dest = 'vc_root', type='string', help = 'Specify an alternate root location for videocache', default = '/')
    parser.add_option('-u', '--squid-user', dest = 'squid_user', type='string', help = 'User who runs Squid daemon.')
    parser.add_option('-a', '--apache-dir', dest = 'apache_dir', type='string', help = 'Path to conf.d directory for Apache. In most cases, it\'ll be /etc/httpd/conf.d/ or /etc/apache2/conf.d/.')
    parser.add_option('-s', '--skip-apache-conf', dest = 'skip_apache_conf', action='store_true', help = 'Skip creating Videocache specific configuration for Apache.', default = False)
    parser.add_option('-c', '--skip-config', dest = 'skip_config', action='store_true', help = 'Skip creating Videocache configuration file.', default = False)
    options, args = parser.parse_args()

    if os.getuid() != 0:
        parser.print_help()
        setup_error('uid')

    if 'install' not in args:
        parser.print_help()
        setup_error('usage')

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
            print_message_and_abort('\nPlease use -u (or --squid-user) option to specify the user who runs Squid daemon.\n')

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
            print_message_and_abort('\nPlease use -a (or --apache-dir) option to specify the path to Apache\'s conf.d directory.\n')
    else:
        apache_dir = options.apache_dir

    if options.vc_root[0] != '/':
        root = os.path.join(os.getcwd(), options.vc_root)
    else:
        root = options.vc_root

    working_dir = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))
    videocache_dir = os.path.join(working_dir, 'videocache')
    config_file = os.path.join(working_dir, 'videocache-sysconfig.conf')
    man_page = os.path.join(working_dir, 'videocache.8.gz')

    if os.path.isdir(videocache_dir):
        sys.path = [videocache_dir] + sys.path
        from vcoptions import VideocacheOptions
        from common import *
        from fsop import *
    else:
        parser.print_help()
        setup_error('usage')

    try:
        o = VideocacheOptions(config_file)
    except Exception, e:
        parser.print_help()
        log_traceback()
        print_message_and_abort('\nvc-setup: Could not read options from configuration file.\n')

    if o.halt:
        parser.print_help()
        print_message_and_abort('\nvc-setup: One or more errors occured in reading configure file. Please check syslog messages generally located at /var/log/messages.\n')

    setup_vc(o, root, options.squid_user, apache_dir, working_dir, not options.verbose, options.skip_config)

