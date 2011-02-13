#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import cgi
import os
import pwd
import shutil
import stat
import sys
import syslog
import time
import traceback
import urllib
import urlparse


def syslog_msg(msg):
    syslog.syslog(syslog.LOG_ERR | syslog.LOG_DAEMON, msg)

def refine_url(url, arg_drop_list = []):
    """Returns a refined url with all the arguments mentioned in arg_drop_list dropped."""
    query = urlparse.urlsplit(url)[3]
    args = cgi.parse_qs(query, True)
    [args.has_key(arg) and args.pop(arg) for arg in arg_drop_list]
    new_args = []
    for (k,v) in args.items():
        if len(v) > 0 and v[0] != '':
            new_args.append(k + '=' + str(v[0]))
        else:
            new_args.append(k)
    new_query = '&'.join(new_args)
    #new_query = '&'.join([k + '=' + str(v[0]) for (k,v) in args.items()])
    return (urllib.splitquery(url)[0] + '?' + new_query.rstrip('&')).rstrip('?')

def build_message(params):
    cur_time = time.time()
    local_time = time.strftime(params.get('timeformat', '%d/%b/%Y:%H:%M:%S'), time.localtime())
    gmt_time = time.strftime(params.get('timeformat', '%d/%b/%Y:%H:%M:%S'), time.gmtime())
    return params.get('logformat', '') % { 'timestamp' : int(cur_time), 'timestamp_ms' : round(cur_time, 3), 'localtime' : local_time, 'gmt_time' : gmt_time, 'process_id' : params.get('process_id', '-'), 'levelname' : params.get('levelname', '-'), 'client_ip' : params.get('client_ip', '-'), 'website_id' : params.get('website_id', '-').upper(), 'code' : params.get('code', '-'), 'video_id' : params.get('video_id', '-'), 'message' : params.get('message', '-'), 'debug' : params.get('debug', '-') }

def get_youtube_video_id(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    dict = cgi.parse_qs(query)
    if dict.has_key('video_id'):
        video_id = dict['video_id'][0]
    elif dict.has_key('docid'):
        video_id = dict['docid'][0]
    elif dict.has_key('id'):
        video_id = dict['id'][0]
    else:
        video_id = None
    return video_id

def get_youtube_video_format(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    dict = cgi.parse_qs(query)
    if dict.has_key('fmt'):
        format_id = dict['fmt'][0]
    elif dict.has_key('itag'):
        format_id = dict['itag'][0]
    else:
        format_id = 34
    return format_id

def proc_test(pid):
    try:
        return os.path.exists("/proc/" + str(pid))
    except Exception, e:
        return None

def is_running(pid):
    import sys
    import errno

    try:
        os.kill(int(pid), 0)
    except OSError, e:
        if e.errno == errno.ESRCH:
            return False
        elif e.errno == errno.EPERM:
            return None
        else:
            return None
    except Exception, e:
        return None
    else:
        return True

# Videocache setup/update specific functions
def log_traceback():
    print '\n' + '-' * 25 + 'Traceback Begin' + '-' * 25
    print traceback.format_exc(),
    print '-' * 25 + 'Traceback End' + '-' * 27 + '\n'

def create_dir(dir, user=None, mode=0755):
    """Create a directory in the filesystem with user:group ownership and mode as permissions."""
    try:
        os.makedirs(dir, mode)
        print "Created : " + dir
    except:
        print "Failed to create : " + dir
        log_traceback()
        return False
    return dir_perms_and_ownership(dir, user, mode)

def dir_perms_and_ownership(dir, user=None, mode=0755):
    """Change the permissions and ownership of a directory."""
    try:
        stats = os.stat(dir)
    except:
        stats = None
    try:
        os.chmod(dir, mode)
    except:
        print "Failed to change permission : " + dir
        log_traceback()

    if user == None:
        return True

    user = pwd.getpwnam(user)[2]

    if stats is not None and stats[stat.ST_UID] == user and stats[stat.ST_GID] == user:
        return True
    try:
        os.chown(dir, user, user)
        print "Ownership changed : " + dir
    except:
        print "Failed to change ownership : " + dir
        log_traceback()
        return False

    return True

def create_file(filename, user=None, mode=0755):
    """Create a file in the filesystem with user:group ownership and mode as permissions."""
    try:
        file(filename, 'a').close()
        print "Created : " + filename
    except:
        print "Failed to create : " + filename
        log_traceback()
        return False
    
    try:
        os.chmod(filename, mode)
        print "Mode changed : " + filename
    except:
        print "Failed to change mode : " + filename
        log_traceback()
        return False

    if user == None:
        return True

    user = pwd.getpwnam(user)[2]

    try:
        os.chown(filename, user, user)
        print "Ownership changed : " + filename
    except:
        print "Failed to change ownership : " + filename
        log_traceback()
        return False
    return True

def copy_file(source, dest):
    """Copies the source file to dest file."""
    try:
        shutil.copy2(source, dest)
        print "Copied : " + source + " > " + dest
    except:
        print "Failed to copy : " + source + " > " + dest
        log_traceback()
        return False
    return True

def copy_dir(source, dest):
    """Copies the source directory recursively to dest dir."""
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
            print "Removed existing : " + dest
    except:
        print "Failed to remove existing : " + dest
        log_traceback()
        return False
    try:
        shutil.copytree(source, dest)
        print "Copied : " + source + " > " + dest
    except:
        print "Failed to copy : " + source + " > " + dest
        log_traceback()
        return False
    return True

def generate_httpd_conf(conf_file, base_dir_list):
    """Generates /etc/httpd/conf.d/videocache.conf for apache web server for serving videos."""
    videocache_conf = """##############################################################################
#                                                                            #
# file : """ + conf_file + " "*(68 - len(conf_file)) + """#
#                                                                            #
# Videocache is a squid url rewriter to cache videos from various websites.  #
# Check http://cachevideos.com/ for more details.                            #
#                                                                            #
# ----------------------------- Note This ---------------------------------- #
# Don't change this file under any circumstances.                            #
# Use /etc/videocache.conf to configure Videocache.                          #
#                                                                            #
##############################################################################\n\n"""
    for dir in base_dir_list:
        if len(base_dir_list) == 1:
            videocache_conf += "Alias /videocache " + dir
        else:
            videocache_conf += "Alias /videocache/" + str(base_dir_list.index(dir)) + " " + dir

        videocache_conf += """
<Directory """ + dir + """>
  Options +Indexes
  Order Allow,Deny
  Allow from all
</Directory>\n"""

    try:
        file = open(conf_file, 'w')
        file.write(videocache_conf)
        file.close()
        print "Generated config file : " + conf_file
    except:
        print "Failed to generate config file : " + conf_file
        log_traceback()
        return False
    return True

def update_error(error_code):
    """Report error while updating/installing videocache with proper error code."""
    help_message =  """
Usage: vc-update (as root/super user)
Update script can only be used if Videocache is installed on your system.
Please see http://cachevideos.com/vc-update for more information or getting help.
"""
    update_error =  """
An error has occured while updating videocache.
Please see http://cachevideos.com/vc-update for more information or getting help.
"""
    uid_error = """
You must be root to update Videocache installation.
Please see http://cachevideos.com/vc-update for more information or getting help.
"""
    if error_code == 'update':
        sys.stderr.write(update_error)
        sys.exit(1)
    if error_code == 'uid':
        sys.stderr.write(uid_error)
        sys.exit(1)
    if error_code == 'usage':
        sys.stderr.write(help_message)
        sys.exit(1)

def update_success():
    """Print informative messages after successfull installation."""
    message = """
Videocache update has completed successfully.
Now you must restart apache web server on your machine by using the following command
[root@localhost ~]# apachectl -k restart [ENTER]
In case of any bugs or problems, check http://cachevideos.com/ .
    """
    print message

def apply_install_root(root, dir):
    """Apply --prefix option to all the directories."""
    return os.path.join(root, dir.strip('/'))

def update_vc(o, root, squid_user, install_dir, apache_conf_dir):
    """Perform the update."""
    etc_dir = apply_install_root(root, '/etc/')
    usr_sbin_dir = apply_install_root(root, '/usr/sbin/')
    var_dir = os.path.dirname(o.scheduler_pidfile)
    man_dir = apply_install_root(root, '/usr/share/man/man8/')

    if apache_conf_dir:
        apache_conf_dir = apply_install_root(root, apache_conf_dir)

    # Create /etc/ directory.
    if not os.path.isdir(etc_dir):
        if not create_dir(etc_dir):
            update_error('update')
    else:
        print "Exists : " + etc_dir

    # Create /usr/sbin/ directory.
    if not os.path.isdir(usr_sbin_dir):
        if not create_dir(usr_sbin_dir):
            update_error('update')
    else:
        print "Exists : " + usr_sbin_dir

    # Create Apache configuration directory.
    if apache_conf_dir:
        if not os.path.isdir(apache_conf_dir):
            if not create_dir(apache_conf_dir):
                update_error('update')
        else:
            print "Exists : " + apache_conf_dir

    # Create /var/run
    if not os.path.isdir(var_dir):
        if not create_dir(var_dir):
            update_error('update')
    else:
        print "Exists : " + var_dir

    # Create man directory.
    if not os.path.isdir(man_dir):
        if not create_dir(man_dir):
            update_error('update')
    else:
        print "Exists : " + man_dir

    # Create videocache log directory.
    if not os.path.isdir(o.logdir):
        if not create_dir(o.logdir, squid_user):
            update_error('update')
    else:
        if not dir_perms_and_ownership(o.logdir, squid_user):
            update_error('update')
        print "Exists : " + o.logdir

    # Create base directories
    for dir in o.base_dir_list:
        if not os.path.isdir(dir):
            if not create_dir(dir, squid_user):
                update_error('update')
        else:
            if not dir_perms_and_ownership(dir, squid_user):
                update_error('update')
            print "Exists : " + dir

    # Create directories for video caching.
    for (website_id, dir_list) in o.base_dirs.items():
        for dir in dir_list:
            if not os.path.isdir(dir):
                if not create_dir(dir, squid_user):
                    update_error('update')
            else:
                if not dir_perms_and_ownership(dir, squid_user):
                    update_error('update')
                print "Exists : " + dir

    # Generate Apache webserver configuration file for videocache.
    if apache_conf_dir and not generate_httpd_conf(os.path.join(apache_conf_dir, 'videocache.conf'), o.base_dir_list):
        update_error('update')

    update_success()
    return

# Videocache Cleaner specific functions
def cleaner_error(error_code):
    """Report error while cleaning videocache with proper error code."""
    help_message =  """
Usage: vc-cleaner -h (as root/super user)
Videocache cleaner script can only be used if Videocache is installed on your system.
Please see http://cachevideos.com/vc-cleaner for more information or getting help.
"""
    uid_error = """
You must be root to run videocache cleaner.
Please see http://cachevideos.com/vc-cleaner for more information or getting help.
"""
    if error_code == 'uid':
        sys.stderr.write(uid_error)
        sys.exit(1)
    if error_code == 'usage':
        sys.stderr.write(help_message)
        sys.exit(1)
    return

# Setup specific functions
def setup_error(error_code):
    """Report error while updating/installing videocache with proper error code."""
    help_message =  """
Usage: python setup.py install (as root/super user)
Please see http://cachevideos.com/installation for more information or getting help.
"""
    install_error =  """
An error has occured while installing videocache.
Please see http://cachevideos.com/installation for more information or getting help.
"""
    uid_error = """
You must be root to setup/install videocache.
Please see http://cachevideos.com/installation for more information or getting help.
"""
    if error_code == 'install':
        sys.stderr.write(install_error)
        sys.exit(1)
    if error_code == 'uid':
        sys.stderr.write(uid_error)
        sys.exit(1)
    if error_code == 'usage':
        sys.stderr.write(help_message)
        sys.exit(1)
    return

def setup_success():
    """Print informative messages after successfull installation."""
    message = """
Videocache setup has completed successfully.
Now you must restart Apache web server on your machine by using the following command
[root@localhost ~]# apachectl -k restart [ENTER]
Also, you need to configure squid so that it can use videocache as a url rewritor plugin.
Check README file for further configurations of squid, httpd and videocache.
In case of any bugs or problems, check http://cachevideos.com/ .
    """
    print message

def setup_vc(o, root, squid_user, apache_conf_dir, working_dir):
    """Perform the setup."""
    install_dir = apply_install_root(root, '/usr/share/videocache/')
    etc_dir = apply_install_root(root, '/etc/')
    usr_sbin_dir = apply_install_root(root, '/usr/sbin/')
    var_dir = os.path.dirname(o.scheduler_pidfile)
    man_dir = apply_install_root(root, '/usr/share/man/man8/')

    if apache_conf_dir:
        apache_conf_dir = apply_install_root(root, apache_conf_dir)

    # Create videocache installation directory.
    if not os.path.isdir(install_dir):
        if not create_dir(install_dir):
            setup_error('install')
    else:
        print "Exists : " + install_dir

    # Create /etc/ directory.
    if not os.path.isdir(etc_dir):
        if not create_dir(etc_dir):
            setup_error('install')
    else:
        print "Exists : " + etc_dir

    # Create /usr/sbin/ directory.
    if not os.path.isdir(usr_sbin_dir):
        if not create_dir(usr_sbin_dir):
            setup_error('install')
    else:
        print "Exists : " + usr_sbin_dir

    # Create Apache configuration directory.
    if apache_conf_dir:
        if not os.path.isdir(apache_conf_dir):
            if not create_dir(apache_conf_dir):
                setup_error('install')
        else:
            print "Exists : " + apache_conf_dir

    # Create /var/run
    if not os.path.isdir(var_dir):
        if not create_dir(var_dir):
            setup_error('install')
    else:
        print "Exists : " + var_dir

    # Create man directory.
    if not os.path.isdir(man_dir):
        if not create_dir(man_dir):
            setup_error('install')
    else:
        print "Exists : " + man_dir

    # Create videocache log directory.
    if not os.path.isdir(o.logdir):
        if not create_dir(o.logdir, squid_user):
            setup_error('install')
    else:
        print "Exists : " + o.logdir
        if not dir_perms_and_ownership(o.logdir, squid_user):
            setup_error('install')

    # Create base directories
    for dir in o.base_dir_list:
        if not os.path.isdir(dir):
            if not create_dir(dir, squid_user):
                setup_error('install')
        else:
            if not dir_perms_and_ownership(dir, squid_user):
                setup_error('install')
            print "Exists : " + dir

    # Create directories for video caching.
    for (website_id, dir_list) in o.base_dirs.items():
        for dir in dir_list:
            if not os.path.isdir(dir):
                if not create_dir(dir, squid_user):
                    setup_error('install')
            else:
                if not dir_perms_and_ownership(dir, squid_user):
                    setup_error('install')
                print "Exists : " + dir

    # Copy core videocache plugin code to /usr/share/videocache/ .
    if not copy_dir(os.path.join(working_dir, 'videocache'), install_dir):
        setup_error('install')

    # Copy videocache-sysconfig.conf to /etc/videocache.conf .
    if not copy_file(os.path.join(working_dir, 'videocache-sysconfig.conf'), os.path.join(etc_dir, 'videocache.conf')):
        setup_error('install')

    # Copy videocache.8.gz (manpage) to /usr/share/man/man8/videocache.8.gz
    if not copy_file(os.path.join(working_dir, 'videocache.8.gz'), os.path.join(man_dir, 'videocache.8.gz')):
        setup_error('install')

    # Generate Apache webserver configuration file for videocache.
    if apache_conf_dir and not generate_httpd_conf(os.path.join(apache_conf_dir, 'videocache.conf'), o.base_dir_list):
        setup_error('install')

    try:
        src_vc_update = os.path.join(install_dir, 'vc-update')
        src_vc_cleaner = os.path.join(install_dir, 'vc-cleaner')
        src_vc_scheduler = os.path.join(install_dir, 'vc-scheduler')
        dst_vc_update = os.path.join(usr_sbin_dir, 'vc-update')
        dst_vc_cleaner = os.path.join(usr_sbin_dir, 'vc-cleaner')
        dst_vc_scheduler = os.path.join(usr_sbin_dir, 'vc-scheduler')

        os.chmod(src_vc_update, 0755)
        os.chmod(src_vc_cleaner, 0755)
        os.chmod(src_vc_scheduler, 0755)

        if os.path.islink(dst_vc_update): os.unlink(dst_vc_update)
        if os.path.islink(dst_vc_cleaner): os.unlink(dst_vc_cleaner)
        if os.path.islink(dst_vc_scheduler): os.unlink(dst_vc_scheduler)

        os.symlink(src_vc_update, dst_vc_update)
        os.symlink(src_vc_cleaner, dst_vc_cleaner)
        os.symlink(src_vc_scheduler, dst_vc_scheduler)
    except Exception, e:
        log_traceback()
        setup_error('install')

    setup_success()
    return

