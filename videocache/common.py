#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import os
import pwd
import shutil
import stat
import sys
import syslog
import time
import urllib
import urlparse


def syslog_msg(msg):
    syslog.syslog(syslog.LOG_ERR | syslog.LOG_DAEMON, msg)

def refine_url(url, arg_drop_list = []):
    """Returns a refined url with all the arguments mentioned in arg_drop_list dropped."""
    query = urlparse.urlsplit(url)[3]
    args = urlparse.parse_qs(query, True)
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

    dict = urlparse.parse_qs(query)
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

    dict = urlparse.parse_qs(query)
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

# Videocache update specific functions
def create_dir(dir, user=None, mode=0755):
    """Create a directory in the filesystem with user:group ownership and mode as permissions."""
    try:
        os.makedirs(dir, mode)
        print "Created directory " + dir + " ."
    except:
        print "Could not create directory " + dir + " ."
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
        print "Could not change permissions of directory " + dir + " ."

    if user == None:
        return True

    user = pwd.getpwnam(user)[2]

    if stats is not None and stats[stat.ST_UID] == user and stats[stat.ST_GID] == user:
        return True
    try:
        os.chown(dir, user, user)
        print "Changed ownership of " + dir + " ."
    except:
        print "Could not change ownership of directory " + dir + " ."
        return False

    return True

def create_file(filename, user=None, mode=0755):
    """Create a file in the filesystem with user:group ownership and mode as permissions."""
    try:
        file(filename, 'a').close()
        print "Created file " + filename + " ."
    except:
        print "Could not create file " + filename + " ."
        return False
    
    try:
        os.chmod(filename, mode)
        print "Changed mode of file " + filename + " ."
    except:
        print "Could not change the mode of the file " + filename + " ."
        return False

    if user == None:
        return True

    user = pwd.getpwnam(user)[2]

    try:
        os.chown(filename, user, user)
        print "Changed ownership of file " + filename + " ."
    except:
        print "Could not change ownership of file " + filename + " ."
        return False
    return True

def copy_file(source, dest):
    """Copies the source file to dest file."""
    try:
        shutil.copy2(source, dest)
        print "Copied file " + source + " to " + dest + " ."
    except:
        print "Could not copy the file " + source + " to file " + dest + " ."
        return False
    return True

def copy_dir(source, dest):
    """Copies the source directory recursively to dest dir."""
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
            print "Removed already existing directory " + dest + " ."
    except:
        print "Could not remove the already existing destination directory " + dest + " ."
        return False
    try:
        shutil.copytree(source, dest)
        print "Copied source directory " + source + " to " + dest + " ."
    except:
        print "Could not copy directory " + source + " to " + dest + " ."
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
        print "Generated config file for Apache webserver in file " + conf_file + " ."
    except:
        print "Could not write config file for apache web server to " + conf_file + " ."
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
        print update_error
        sys.exit(1)
    if error_code == 'uid':
        print uid_error
        sys.exit(1)
    if error_code == 'usage':
        print help_message
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

def update_vc(o, root, install_dir, apache_conf_dir):
    """Perform the update."""
    etc_dir = apply_install_root(root, '/etc/')
    usr_sbin_dir = apply_install_root(root, '/usr/sbin/')
    apache_conf_dir = apply_install_root(root, apache_conf_dir)
    var_dir = apply_install_root(root, os.path.dirname(o.scheduler_logfile))
    man_dir = apply_install_root(root, '/usr/share/man/man8/')

    # Create /etc/ directory.
    if not os.path.isdir(etc_dir):
        if not create_dir(etc_dir):
            update_error('update')
    else:
        print "Directory " + etc_dir + " already exists."

    # Create /usr/sbin/ directory.
    if not os.path.isdir(usr_sbin_dir):
        if not create_dir(usr_sbin_dir):
            update_error('update')
    else:
        print "Directory " + usr_sbin_dir + " already exists."

    # Create Apache configuration directory.
    if not os.path.isdir(apache_conf_dir):
        if not create_dir(apache_conf_dir):
            update_error('update')
    else:
        print "Directory " + apache_conf_dir + " already exists."

    # Create /var/run
    if not os.path.isdir(var_dir):
        if not create_dir(var_dir):
            update_error('update')
    else:
        print "Directory " + var_dir + " already exists."

    # Create man directory.
    if not os.path.isdir(man_dir):
        if not create_dir(man_dir):
            update_error('update')
    else:
        print "Directory " + man_dir + " already exists."

    # Create videocache log directory.
    if not os.path.isdir(o.logdir):
        if not create_dir(o.logdir, o.videocache_user):
            update_error('update')
    else:
        print "Directory " + o.logdir + " already exists."

    # Create base directories
    for dir in o.base_dir_list:
        if not os.path.isdir(dir):
            if not create_dir(dir, o.videocache_user):
                update_error('update')
        else:
            if not dir_perms_and_ownership(dir, o.videocache_user):
                update_error('update')
            print "Directory " + dir + " already exists."

    # Create directories for video caching.
    for (website_id, dir_list) in o.base_dirs.items():
        for dir in dir_list:
            if not os.path.isdir(dir):
                if not create_dir(dir, o.videocache_user):
                    update_error('update')
            else:
                if not dir_perms_and_ownership(dir, o.videocache_user):
                    update_error('update')
                print "Directory " + dir + " already exists."

    # Generate Apache webserver configuration file for videocache.
    if not generate_httpd_conf(os.path.join(apache_conf_dir, 'videocache.conf'), o.base_dir_list):
        update_error('update')

    update_success()

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
        print uid_error
        sys.exit(1)
    if error_code == 'usage':
        print help_message
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
        print install_error
        sys.exit(1)
    if error_code == 'uid':
        print uid_error
        sys.exit(1)
    if error_code == 'usage':
        print help_message
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

def setup_vc(o, root, apache_conf_dir, working_dir):
    """Perform the setup."""
    install_dir = apply_install_root(root, '/usr/share/videocache/')
    etc_dir = apply_install_root(root, '/etc/')
    usr_sbin_dir = apply_install_root(root, '/usr/sbin/')
    apache_conf_dir = apply_install_root(root, apache_conf_dir)
    var_dir = apply_install_root(root, os.path.dirname(o.scheduler_logfile))
    man_dir = apply_install_root(root, '/usr/share/man/man8/')

    # Create videocache installation directory.
    if not os.path.isdir(install_dir):
        if not create_dir(install_dir):
            setup_error('install')
    else:
        log(format%("Directory " + install_dir + " already exists."))

    # Create /etc/ directory.
    if not os.path.isdir(etc_dir):
        if not create_dir(etc_dir):
            update_error('update')
    else:
        print "Directory " + etc_dir + " already exists."

    # Create /usr/sbin/ directory.
    if not os.path.isdir(usr_sbin_dir):
        if not create_dir(usr_sbin_dir):
            update_error('update')
    else:
        print "Directory " + usr_sbin_dir + " already exists."

    # Create Apache configuration directory.
    if not os.path.isdir(apache_conf_dir):
        if not create_dir(apache_conf_dir):
            update_error('update')
    else:
        print "Directory " + apache_conf_dir + " already exists."

    # Create /var/run
    if not os.path.isdir(var_dir):
        if not create_dir(var_dir):
            update_error('update')
    else:
        print "Directory " + var_dir + " already exists."

    # Create man directory.
    if not os.path.isdir(man_dir):
        if not create_dir(man_dir):
            update_error('update')
    else:
        print "Directory " + man_dir + " already exists."

    # Create base directories
    for dir in o.base_dir_list:
        if not os.path.isdir(dir):
            if not create_dir(dir, o.videocache_user):
                update_error('update')
        else:
            if not dir_perms_and_ownership(dir, o.videocache_user):
                update_error('update')
            print "Directory " + dir + " already exists."

    # Create directories for video caching.
    for (website_id, dir_list) in o.base_dirs.items():
        for dir in dir_list:
            if not os.path.isdir(dir):
                if not create_dir(dir, o.videocache_user):
                    update_error('update')
            else:
                if not dir_perms_and_ownership(dir, o.videocache_user):
                    update_error('update')
                print "Directory " + dir + " already exists."

    # Copy core videocache plugin code to /usr/share/videocache/ .
    if not copy_dir(videocache_dir, install_dir):
        setup_error('install')

    # Copy videocache-sysconfig.conf to /etc/videocache.conf .
    if not copy_file(os.path.join(working_dir, 'videocache-sysconfig.conf'), os.path.join(etc_dir, 'videocache.conf')):
        setup_error('install')

    # Copy videocache.8.gz (manpage) to /usr/share/man/man8/videocache.8.gz
    if not copy_file(os.path.join(working_dir, 'videocache.8.gz'), os.path.join(man_dir, 'videocache.8.gz')):
        setup_error('install')

    # Generate Apache webserver configuration file for videocache.
    if not generate_httpd_conf(os.path.join(apache_conf_dir, 'videocache.conf'), o.base_dir_list):
        setup_error('install')

    try:
        # Copy vccleaner to /usr/sbin/vccleaner
        os.chmod(os.path.join(install_dir, 'vc-cleaner'), 0755)
        os.chmod(os.path.join(install_dir, 'vc-update'), 0755)
        os.chmod(os.path.join(install_dir, 'vc-cleaner'), 0755)
        os.symlink(os.path.join(install_dir, 'vc-cleaner'), os.path.join(usr_sbin_dir, 'vc-cleaner'))
        os.symlink(os.path.join(install_dir, 'vc-update'), os.path.join(usr_sbin_dir, 'vc-update'))
        os.symlink(os.path.join(install_dir, 'vc-scheduler'), os.path.join(usr_sbin_dir, 'vc-scheduler'))
    except Exception, e:
        setup_error('install')

    setup_success()

