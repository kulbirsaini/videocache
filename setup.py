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

def red(msg):#{{{
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
    print blue('-' * 25 + 'Traceback End' + '-' * 27 + '\n')#}}}

# Setup specific functions
def setup_error(error_code):#{{{
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
--squid-store-log   Full path to Squid store.log file. Example: /var/log/squid/store.log
--apache-conf-dir   Full path to conf.d or extra directory for Apache.
                    Example: /etc/httpd/conf.d/ or /etc/apache2/conf.d/ or /etc/httpd/extra/

You must supply either --skip-apache-conf or --apache-conf-dir.
To see a list of all available options, please run
$ python setup.py -h

Usage: python setup.py -e a@b.me -u squid --cache-host 10.1.1.1 --this-proxy 127.0.0.1:3128 --squid-store-log /var/log/squid/store.log --apache-conf-dir /etc/httpd/conf.d install --db-hostname localhost --db-username videocache --db-password videocache --db-database videocache

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
    messages['squid_store_log'] = "(--squid-store-log)  Squid store.log file path specified using --squid-store-log option doesn't start with a /"
    if error_code in messages:
        return messages[error_code]
    return ''#}}}

def setup_vc(o, root, email, user, skip_vc_conf, apache_conf_dir, cache_host, this_proxy, squid_store_log, quiet, working_dir, skip_db, hostname, username, password, database):#{{{
    """Perform the setup."""
    install_dir = apply_install_root(root, '/usr/share/videocache/')
    etc_dir = apply_install_root(root, '/etc/')
    usr_sbin_dir = apply_install_root(root, '/usr/sbin/')
    var_dir = os.path.dirname(o.scheduler_pidfile)
    init_dir = apply_install_root(root, '/etc/init.d/')

    install_error = blue("\n\n" + setup_error('install'))

    dirs_to_be_created = [install_dir, etc_dir, usr_sbin_dir, var_dir, init_dir]

    if apache_conf_dir != '':
        dirs_to_be_created += [apply_install_root(root, apache_conf_dir)]

    for dir in dirs_to_be_created:
        if not create_or_update_dir(dir, None, 0755, quiet):
            print_message_and_abort(red("Could not create directory %s" % dir) + install_error)

    for dir in sum([o.base_dir_list] + [[o.logdir]] + [v for (k, v) in o.base_dirs.items()], []):
        if not create_or_update_dir(dir, user, 0755, quiet):
            print_message_and_abort(red("Could not create directory %s" % dir) + install_error)

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
        if skip_db:
            use_db = 0
        else:
            use_db = 1
        config_data = re.sub('\nvideocache_user[\ ]*=[^\n]*\n', '\nvideocache_user = %s\n' % user, config_data, count = 0)
        config_data = re.sub('\nclient_email[\ ]*=[^\n]*\n', '\nclient_email = %s\n' % email, config_data, count = 0)
        config_data = re.sub('\ncache_host[\ ]*=[^\n]*\n', '\ncache_host = %s\n' % cache_host, config_data, count = 0)
        config_data = re.sub('\nthis_proxy[\ ]*=[^\n]*\n', '\nthis_proxy = %s\n' % this_proxy, config_data, count = 0)
        config_data = re.sub('\nsquid_store_log[\ ]*=[^\n]*\n', '\nsquid_store_log = %s\n' % squid_store_log, config_data, count = 0)
        config_data = re.sub('\napache_conf_dir[\ ]*=[^\n]*\n', '\napache_conf_dir = %s\n' % apache_conf_dir, config_data, count = 0)
        config_data = re.sub('\nuse_db[\ ]*=[^\n]*\n', '\nuse_db = %d\n' % use_db, config_data, count = 0)
        config_data = re.sub('\ndb_hostname[\ ]*=[^\n]*\n', '\ndb_hostname = %s\n' % hostname, config_data, count = 0)
        config_data = re.sub('\ndb_username[\ ]*=[^\n]*\n', '\ndb_username = %s\n' % username, config_data, count = 0)
        config_data = re.sub('\ndb_password[\ ]*=[^\n]*\n', '\ndb_password = %s\n' % password, config_data, count = 0)
        config_data = re.sub('\ndb_database[\ ]*=[^\n]*\n', '\ndb_database = %s\n' % database, config_data, count = 0)
        if apache_conf_dir == '':
            skip_apache_conf = 1
        else:
            skip_apache_conf = 0
        config_data = re.sub('\nskip_apache_conf[\ ]*=[^\n]*\n', '\nskip_apache_conf = %s\n' % skip_apache_conf, config_data, count = 0)
        file.write(config_data)
        file.close()

    # Copy vc-scheduler.rc to /etc/init.d/
    if not copy_file(os.path.join(working_dir, 'vc-scheduler.rc'), os.path.join(init_dir, 'vc-scheduler'), quiet):
        print_message_and_abort(red("Could not copy Videocache scheduler init file to %s" % os.path.join(init_dir, 'vc-scheduler')) + install_error)

    # Generate Apache webserver configuration file for videocache.
    if apache_conf_dir and not generate_httpd_conf(os.path.join(apache_conf_dir, 'videocache.conf'), o.base_dir_list, cache_host, True, quiet):
        print_message_and_abort(red("Could not generate Apache specific configuration file at %s" % os.path.join(apache_conf_dir, 'videocache.conf')) + install_error)

    # Create tables for filelist database
    try:
        if not skip_db:
            initialize_database(o)
            if not create_tables():
                print_message_and_abort(red("Could not create database tables for filelist db"))
    except Exception, e:
        log_traceback()
        print_message_and_abort(install_error)

    generate_magnet_http(os.path.join(working_dir, 'videocache', 'vcconfig.py'), os.path.join(install_dir, 'vcconfig.py'))

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

    squid_config_lines = "cache_store_log %s\nacl this_machine src 127.0.0.1 %s \nhttp_access allow this_machine" % (squid_store_log, get_ip_addresses().replace(',', ' '))
    msg = """
Setup has completed successfully. Plesae follow the following steps to start Videocache.

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

Also add the following lines at the top of your Squid config file squid.conf.
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

Check Manual.pdf file for detailed configurations of squid, apache and videocache.
In case of any bugs or problems, visit http://cachevideos.com/ and contact us.""" % squid_config_lines

    file = open(os.path.join(working_dir, 'instructions.txt'), 'w')
    file.write(msg)
    file.close
    return#}}}

def process_options(parser):#{{{
    parser.add_option('-v', '--verbose', dest = 'verbose', action='store_true', help = 'Print detailed log messages.', default = False)
    parser.add_option('-p', '--prefix', dest = 'vc_root', type='string', help = 'Specify an alternate root location for videocache', default = '/')
    parser.add_option('-e', '--client-email', dest = 'client_email', type='string', help = 'Email address using which Videocache was purchased.')
    parser.add_option('-u', '--squid-user', dest = 'squid_user', type='string', help = 'User who runs Squid daemon.')
    parser.add_option('--skip-vc-conf', dest = 'skip_vc_conf', action='store_true', help = 'Skip creating Videocache configuration file.', default = False)
    parser.add_option('--skip-apache-conf', dest = 'skip_apache_conf', action='store_true', help = 'Skip creating Videocache specific configuration for Apache.', default = False)
    parser.add_option('--apache-conf-dir', dest = 'apache_conf_dir', type='string', help = 'Path to conf.d directory for Apache. In most cases, it\'ll be /etc/httpd/conf.d/ or /etc/apache2/conf.d/.')
    parser.add_option('--cache-host', dest = 'cache_host', type='string', help = 'Cache host (IP Address with optional port) to serve cached videos via Apache.')
    parser.add_option('--this-proxy', dest = 'this_proxy', type='string', help = 'Squid proxy server on this machine (IPADDRESS:PORT).')
    parser.add_option('--squid-store-log', dest = 'squid_store_log', type='string', help = 'Full path to Squid store.log file. Example : /var/log/squid/store.log')
    parser.add_option('--skip-db', dest = 'skip_db', action='store_true', help = 'Skip database setup.', default = False)
    parser.add_option('--db-hostname', dest = 'db_hostname', type='string', help = 'Enter hostname for database access')
    parser.add_option('--db-username', dest = 'db_username', type='string', help = 'Enter username for database access')
    parser.add_option('--db-password', dest = 'db_password', type='string', help = 'Enter password for database access')
    parser.add_option('--db-database', dest = 'db_database', type='string', help = 'Enter database name for videocache')
    return parser.parse_args()#}}}

def is_valid_path(path, file = True):#{{{
    if file and path.endswith('/'):
        return False
    if re.compile('^/([^\/]+\/){1,7}[^\/]+\/?$').match(path):
        return True
    return False#}}}

def verify_options(options, args):#{{{
    if os.geteuid() != 0:
        print_message_and_abort(red(setup_error('uid')))

    if 'install' not in args or not options.client_email or not options.squid_user or not options.cache_host or not options.this_proxy or not options.squid_store_log or (options.skip_apache_conf == False and not options.apache_conf_dir):
        print_message_and_abort(red(setup_error('usage')))

    messages = ''
    if not is_valid_host_port(options.cache_host, port_optional = True):
        messages += "\n\n" + setup_error('cache_host')

    if not is_valid_host_port(options.this_proxy):
        messages += "\n\n" + setup_error('this_proxy')

    if not options.skip_apache_conf and not is_valid_path(options.apache_conf_dir, False):
        messages += "\n\n" + setup_error('apache_conf_dir')

    if not is_valid_email(options.client_email):
        messages += "\n\n" + setup_error('client_email')

    if not is_valid_user(options.squid_user):
        messages += "\n\n" + setup_error('squid_user')

    if not is_valid_path(options.squid_store_log):
        messages += "\n\n" + setup_error('squid_store_log')

    if messages != '':
        messages = blue("One or more validation errors occurred. Please fix them and try running setup.py again.\n") + red(messages) + "\n"
        print_message_and_abort(messages)
    return#}}}

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
            from vcsysinfo import get_ip_addresses
            from database import create_tables, initialize_database
        except Exception, e:
            log_traceback()
            print_message_and_abort(red("\nCould not import required modules for setup.") + green("\nIf you contact us regarding this error, please send the Trace above."))
    else:
        print_message_and_abort(red("Could not locate the videocache directory in bundle.\n%s" % setup_error('usage')))

    verify_options(options, args)

    if options.skip_apache_conf:
        options.apache_conf_dir = ''

    if options.skip_db:
        options.db_hostname = ''
        options.db_username = ''
        options.db_password = ''
        options.db_database = ''

    if options.vc_root[0] != '/':
        root = os.path.join(os.getcwd(), options.vc_root)
    else:
        root = options.vc_root

    try:
        o = VideocacheOptions(config_file)
    except Exception, e:
        log_traceback()
        print_message_and_abort(red("\nCould not read options from configuration file located at %s ." % config_file) + green("\nIf you contact us regarding this error, please send the Trace above."))

    if o.halt:
        print_message_and_abort(red('\nOne or more errors occured in reading configuration file.\nPlease check syslog messages generally located at /var/log/messages.') + green("\nIf you contact us regarding this error, please send the log messages."))

    email, user, skip_vc_conf, apache_conf_dir, cache_host, this_proxy, squid_store_log, verbose, skip_db, hostname, username, password, database = options.client_email, options.squid_user, options.skip_vc_conf, options.apache_conf_dir, options.cache_host, options.this_proxy, options.squid_store_log, options.verbose, options.skip_db, options.db_hostname, options.db_username, options.db_password, options.db_database
    setup_vc(o, root, email, user, skip_vc_conf, apache_conf_dir, cache_host, this_proxy, squid_store_log, not verbose, working_dir, skip_db, hostname, username, password, database)

