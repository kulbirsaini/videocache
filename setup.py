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
import re
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
Usage: python setup.py [options] install

Following options must be specified while installing Videocache.
-e --client-email   Email address used to purchase Videocache.
-u --squid-user     User who runs Squid daemon on your system.
--cache-host        IP address with optional port. This will be used as a web server to serve cached videos.
                    Example: 192.168.1.14 or 192.168.1.14:81
--this-proxy        IP_Address:PORT combination for Squid proxy running on this machine.
                    Example: 127.0.0.1:3128 192.168.1.1:8080
--apache-conf-dir   Full path to conf.d or extra directory for Apache.
                    Example: /etc/httpd/conf.d/ or /etc/apache2/conf.d/ or /etc/httpd/extra/

You must supply either --skip-apache-conf or --apache-conf-dir.
To see a list of all available options, please run
$ python setup.py -h

Usage: python setup.py -e a@b.me -u squid --cache-host 10.1.1.1 --this-proxy 127.0.0.1:3128 --apache-conf-dir /etc/httpd/conf.d install

Please see http://cachevideos.com/#install for more information or getting help.
"""

    messages['install'] =  """An error has occured while installing videocache.
Please fix the error and try installing again.

Please see http://cachevideos.com/#install for more information or getting help."""

    messages['uid'] = """
You must run Videocache installer as root or with sudo.
Please see http://cachevideos.com/#install for more information or getting help.
"""

    messages['cache_host'] = """(--cache-host)       Cache host supplied with --cache-host option is not in valid format.
                     Acceptable formats: IP_ADDRESS, IP_ADDRESS:PORT.
                     Examples: 192.168.1.14, 192.168.1.14:81"""

    messages['this_proxy'] = """(--this-proxy)       Squid proxy supplied with --this-proxy option is not in valid format.
                     Acceptable format: IP_ADDRESS:PORT.
                     Examples: 127.0.0.1:3128, 192.168.1.14:8080"""

    messages['apache_conf_dir'] = "(--apache-conf-dir)  Apache conf.d or extra directory specified using --apache-conf-dir option doesn't start with a /"
    messages['client_email'] = "(--client-email)     Email address provided using --client-email option is not in valid format."
    messages['squid_user'] = "(--squid-user)       The user provided using --squid-user option doesn't exist on system."
    if error_code in messages:
        return messages[error_code]
    return ''

def setup_vc(o, email, user, skip_vc_conf, apache_conf_dir, cache_host, this_proxy, quiet, working_dir):
    """Perform the setup."""
    install_dir = '/usr/share/videocache/'
    etc_dir = '/etc/'
    usr_sbin_dir = '/usr/sbin/'
    init_dir = '/etc/init.d/'

    install_error = blue("\n\n" + setup_error('install'))

    dirs_to_be_created = [install_dir, etc_dir, usr_sbin_dir, init_dir]

    if apache_conf_dir != '':
        dirs_to_be_created += [apache_conf_dir]

    for dir in dirs_to_be_created:
        if not create_or_update_dir(dir, None, 0755, quiet):
            print_message_and_abort(red("Could not create directory %s" % dir) + install_error)

    for dir in sum([o.base_dir_list] + [[o.logdir, os.path.join(o.logdir, '.lock')]] + [v for (k, v) in o.base_dirs.items()], []):
        if not create_or_update_dir(dir, user, 0755, quiet):
            print_message_and_abort(red("Could not create directory %s" % dir) + install_error)

    # move pidfile.txt to lock dir
    if os.path.isfile(os.path.join(o.logdir, o.pidfile)):
        move_file(os.path.join(o.logdir, o.pidfile), o.pidfile_path, quiet)

    # Copy core videocache plugin code to /usr/share/videocache/ .
    if not copy_dir(os.path.join(working_dir, 'videocache'), install_dir, quiet):
        print_message_and_abort(red("Could not copy Videocache to installation directory %s" % install_dir) + install_error)

    if not set_permissions_and_ownership(install_dir, user, 0755, quiet):
        print_message_and_abort(red("Could not set ownership and permissions for installation directory %s" % install_dir) + install_error)

    for filename in os.listdir(install_dir):
        filepath = os.path.join(install_dir, filename)
        if not set_permissions_and_ownership(filepath, user, 0755, quiet):
            print_message_and_abort(red("Could not set ownership and permissions for file %s" % filepath) + install_error)

    # Copy videocache-sysconfig.conf to /etc/videocache.conf .
    if not skip_vc_conf:
        vcsysconfig_file = os.path.join(etc_dir, 'videocache.conf')
        if not copy_file(os.path.join(working_dir, 'videocache-sysconfig.conf'), vcsysconfig_file, quiet):
            print_message_and_abort(red("Could not copy Videocache config file to %s" % vcsysconfig_file) + install_error)

        file = open(vcsysconfig_file, 'r')
        config_data = file.read()
        file.close()
        file = open(vcsysconfig_file, 'w')
        config_data = re.sub(r'\nvideocache_user[\ ]*=[^\n]*\n', r'\nvideocache_user = %s\n' % user, config_data, count = 0)
        config_data = re.sub(r'\nclient_email[\ ]*=[^\n]*\n', r'\nclient_email = %s\n' % email, config_data, count = 0)
        config_data = re.sub(r'\ncache_host[\ ]*=[^\n]*\n', r'\ncache_host = %s\n' % cache_host, config_data, count = 0)
        config_data = re.sub(r'\nthis_proxy[\ ]*=[^\n]*\n', r'\nthis_proxy = %s\n' % this_proxy, config_data, count = 0)
        config_data = re.sub(r'\napache_conf_dir[\ ]*=[^\n]*\n', r'\napache_conf_dir = %s\n' % apache_conf_dir, config_data, count = 0)
        if apache_conf_dir == '':
            skip_apache_conf = 1
        else:
            skip_apache_conf = 0
        config_data = re.sub(r'\nskip_apache_conf[\ ]*=[^\n]*\n', r'\nskip_apache_conf = %s\n' % skip_apache_conf, config_data, count = 0)
        file.write(config_data)
        file.close()

    # Copy vc-scheduler.rc to /etc/init.d/
    if not copy_file(os.path.join(working_dir, 'vc-scheduler.rc'), os.path.join(init_dir, 'vc-scheduler'), quiet):
        print_message_and_abort(red("Could not copy Videocache scheduler init file to %s" % os.path.join(init_dir, 'vc-scheduler')) + install_error)

    # Generate Apache webserver configuration file for videocache.
    if apache_conf_dir and not generate_httpd_conf(os.path.join(apache_conf_dir, 'videocache.conf'), o.base_dir_list, cache_host, True, quiet):
        print_message_and_abort(red("Could not generate Apache specific configuration file at %s" % os.path.join(apache_conf_dir, 'videocache.conf')) + install_error)

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
        print_message_and_abort(install_error)

    squid_config_lines = "acl this_machine src 127.0.0.1 %s \nhttp_access allow this_machine" % (get_interface_details()['mac_addresses'].replace(',', ' '))
    msg = """
----------------------------------Step 1-----------------------------------------
Open the Videocache configuration file located at /etc/videocache.conf and modify
any options you want. Once you are done, save the file.

----------------------------------Step 2-----------------------------------------
Run vc-update command to update your installation in accordance with new options.
[root@localhost ~]# vc-update

----------------------------------Step 3-----------------------------------------
Restart Apache web server on your machine by using the following command
[root@localhost ~]# apachectl -k restart

----------------------------------Step 4-----------------------------------------
Depending on the version of your Squid, open vc_squid_2.conf or vc_squid_3.conf
in your Videocache bundle. Copy all the lines and paste them at the top of your
Squid configuration file squid.conf.

Also, add the following lines at the top of your Squid config file squid.conf.
#-----------------CUT FROM HERE-------------------
%s
#-----------------CUT TILL HERE-------------------

----------------------------------Step 5-----------------------------------------
Restart videocache scheduler vc-scheduler using the following command.
[root@localhost ~]# vc-scheduler -s restart

----------------------------------Step 6-----------------------------------------
Restart Squid proxy server daemon using the following command.
[root@localhost ~]# /etc/init.d/squid restart

----------------------------------Step 7-----------------------------------------
Go the videocache log directory /var/log/videocache/ and check various log files
to have a look at videocache activity.

In case of any bugs or problems, visit http://cachevideos.com/ and contact us.
""" % squid_config_lines

    file = open(os.path.join(working_dir, 'instructions.txt'), 'w')
    file.write(msg)
    file.close
    return

def process_options(parser):
    parser.add_option('-v', '--verbose', dest = 'verbose', action='store_true', help = 'Print detailed log messages.', default = False)
    parser.add_option('-e', '--client-email', dest = 'client_email', type='string', help = 'Email address using which Videocache was purchased.')
    parser.add_option('-u', '--squid-user', dest = 'squid_user', type='string', help = 'User who runs Squid daemon.')
    parser.add_option('--skip-vc-conf', dest = 'skip_vc_conf', action='store_true', help = 'Skip creating Videocache configuration file.', default = False)
    parser.add_option('--skip-apache-conf', dest = 'skip_apache_conf', action='store_true', help = 'Skip creating Videocache specific configuration for Apache.', default = False)
    parser.add_option('--apache-conf-dir', dest = 'apache_conf_dir', type='string', help = 'Path to conf.d directory for Apache. In most cases, it\'ll be /etc/httpd/conf.d/ or /etc/apache2/conf.d/.')
    parser.add_option('--cache-host', dest = 'cache_host', type='string', help = 'Cache host (IP Address with optional port) to serve cached videos via Apache.')
    parser.add_option('--this-proxy', dest = 'this_proxy', type='string', help = 'Squid proxy server on this machine (IPADDRESS:PORT).', default = '127.0.0.1:3128')
    return parser.parse_args()

def is_valid_path(path, is_file = True):
    if is_file and path.endswith('/'):
        return False
    if re.compile('^/([^\/]+\/){1,7}[^\/]+\/?$').match(path):
        return True
    return False

def verify_options(options, args):
    if os.geteuid() != 0:
        print_message_and_abort(red(setup_error('uid')))

    if not ('install' in args and options.client_email and options.squid_user and options.cache_host and options.this_proxy and (options.skip_apache_conf or options.apache_conf_dir)):
        print_message_and_abort(red(setup_error('usage')))

    messages = ''
    if not is_valid_host_port(options.cache_host, port_optional = True):
        messages += "\n\n" + setup_error('cache_host')

    if not is_valid_host_port(options.this_proxy):
        messages += "\n\n" + setup_error('this_proxy')

    if not (options.skip_apache_conf or is_valid_path(options.apache_conf_dir, False)):
        messages += "\n\n" + setup_error('apache_conf_dir')

    if not is_valid_email(options.client_email):
        messages += "\n\n" + setup_error('client_email')

    if not is_valid_user(options.squid_user):
        messages += "\n\n" + setup_error('squid_user')

    if messages != '':
        messages = blue("One or more validation errors occurred. Please fix them and try running setup.py again.\n") + red(messages) + "\n"
        print_message_and_abort(messages)
    return

if __name__ == '__main__':
    # Parse command line options.
    parser = OptionParser()
    options, args = process_options(parser)

    working_dir = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))
    videocache_dir = os.path.join(working_dir, 'videocache')
    config_file = os.path.join(working_dir, 'videocache-sysconfig.conf')

    if os.path.isdir(videocache_dir):
        try:
            sys.path = [videocache_dir] + sys.path
            from vcoptions import VideocacheOptions
            from common import *
            from fsop import *
            from vcsysinfo import get_interface_details
        except Exception, e:
            log_traceback()
            print_message_and_abort(red("\nCould not import required modules for setup.") + green("\nIf you contact us regarding this error, please send the Trace above."))
    else:
        print_message_and_abort(red("Could not locate the videocache directory in bundle.\n%s" % setup_error('usage')))

    verify_options(options, args)

    if options.skip_apache_conf:
        options.apache_conf_dir = ''

    try:
        o = VideocacheOptions(config_file, True, True)
    except Exception, e:
        log_traceback()
        print_message_and_abort(red("\nCould not read options from configuration file located at %s ." % config_file) + green("\nIf you contact us regarding this error, please send the Trace above."))

    if o.halt:
        print_message_and_abort(red('\nOne or more errors occured in reading configuration file.\nPlease check syslog messages generally located at /var/log/messages.') + green("\nIf you contact us regarding this error, please send the log messages."))

    email, user, skip_vc_conf, apache_conf_dir, cache_host, this_proxy, verbose = options.client_email, options.squid_user, options.skip_vc_conf, options.apache_conf_dir, options.cache_host, options.this_proxy, options.verbose
    setup_vc(o, email, user, skip_vc_conf, apache_conf_dir, cache_host, this_proxy, not verbose, working_dir)
