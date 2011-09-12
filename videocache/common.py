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
import socket
import stat
import sys
import syslog
import time
import traceback
import urllib
import urllib2
import urlparse


def syslog_msg(msg):
    syslog.syslog(syslog.LOG_ERR | syslog.LOG_DAEMON, msg)

def build_message(params):
    cur_time = time.time()
    local_time = time.strftime(params.get('timeformat', '%d/%b/%Y:%H:%M:%S'), time.localtime())
    gmt_time = time.strftime(params.get('timeformat', '%d/%b/%Y:%H:%M:%S'), time.gmtime())
    return params.get('logformat', '') % { 'timestamp' : int(cur_time), 'timestamp_ms' : round(cur_time, 3), 'localtime' : local_time, 'gmt_time' : gmt_time, 'process_id' : params.get('process_id', '-'), 'levelname' : params.get('levelname', '-'), 'client_ip' : params.get('client_ip', '-'), 'website_id' : params.get('website_id', '-').upper(), 'code' : params.get('code', '-'), 'video_id' : params.get('video_id', '-'), 'size' : params.get('size', '-'), 'message' : params.get('message', '-'), 'debug' : params.get('debug', '-') }

def refine_url(url, arg_drop_list = []):
    """Returns a refined url with all the arguments mentioned in arg_drop_list dropped."""
    if len(arg_drop_list) == 0:
        return url
    query = urlparse.urlsplit(url)[3]
    new_query = '&'.join(['='.join(j) for j in filter(lambda x: x[0] not in arg_drop_list, [i.split('=') for i in query.split('&')])])
    return (urllib.splitquery(url)[0] + '?' + new_query.rstrip('&')).rstrip('?')

# Functions related to Youtube video ID and video format
def get_youtube_video_id_from_query(query):
    dict = cgi.parse_qs(query)
    if 'video_id' in dict:
        video_id = dict['video_id'][0]
    elif 'docid' in dict:
        video_id = dict['docid'][0]
    elif 'id' in dict:
        video_id = dict['id'][0]
    elif 'v' in dict:
        video_id = dict['v'][0]
    else:
        video_id = None
    return video_id

def get_youtube_video_id(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_id_from_query(query)

def get_youtube_video_format_from_query(query):
    dict = cgi.parse_qs(query)
    if 'itag' in dict:
        format = dict['itag'][0]
    elif 'fmt' in dict:
        format = dict['fmt'][0]
    elif 'layout' in dict and dict['layout'][0].lower() == 'mobile':
        format = '18'
    else:
        format = 34
    try:
        format = int(format)
    except:
        format = 34
    return int(format)

def get_youtube_video_format(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_format_from_query(query)

# Test if a process is running or not.
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

def create_dir(dir, user=None, mode=0755, quiet = False):
    """Create a directory in the filesystem with user:group ownership and mode as permissions."""
    try:
        os.makedirs(dir, mode)
        if not quiet: print "Created : " + dir
    except:
        if not quiet: print "Failed to create : " + dir
        log_traceback()
        return False
    return dir_perms_and_ownership(dir, user, mode, quiet)

def dir_perms_and_ownership(dir, user=None, mode=0755, quiet = False):
    """Change the permissions and ownership of a directory."""
    try:
        os.chmod(dir, mode)
    except:
        if not quiet: print "Failed to change permission : " + dir
        log_traceback()

    if user == None:
        return True

    user = pwd.getpwnam(user)

    try:
        stats = os.stat(dir)
    except:
        stats = None
    if stats is not None and stats[stat.ST_UID] == user.pw_uid and stats[stat.ST_GID] == user.pw_gid:
        return True
    try:
        os.chown(dir, user.pw_uid, user.pw_gid)
        if not quiet: print "Ownership changed : " + dir
    except:
        if not quiet: print "Failed to change ownership : " + dir
        log_traceback()
        return False

    return True

def create_file(filename, user=None, mode=0755, quiet = False):
    """Create a file in the filesystem with user:group ownership and mode as permissions."""
    try:
        file(filename, 'a').close()
        if not quiet: print "Created : " + filename
    except:
        if not quiet: print "Failed to create : " + filename
        log_traceback()
        return False
    
    return file_perms_and_ownership(filename, user, mode, quiet)

def file_perms_and_ownership(filename, user=None, mode=0755, quiet = False):
    try:
        os.chmod(filename, mode)
        if not quiet: print "Mode changed : " + filename
    except:
        if not quiet: print "Failed to change mode : " + filename
        log_traceback()
        return False

    if user == None:
        return True

    user = pwd.getpwnam(user)

    try:
        os.chown(filename, user.pw_uid, user.pw_gid)
        if not quiet: print "Ownership changed : " + filename
    except:
        if not quiet: print "Failed to change ownership : " + filename
        log_traceback()
        return False
    return True

def copy_file(source, dest, quiet = False):
    """Copies the source file to dest file."""
    try:
        shutil.copy2(source, dest)
        if not quiet: print "Copied : " + source + " > " + dest
    except:
        if not quiet: print "Failed to copy : " + source + " > " + dest
        log_traceback()
        return False
    return True

def copy_dir(source, dest, quiet = False):
    """Copies the source directory recursively to dest dir."""
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
            if not quiet: print "Removed existing : " + dest
    except:
        if not quiet: print "Failed to remove existing : " + dest
        log_traceback()
        return False
    try:
        shutil.copytree(source, dest)
        if not quiet: print "Copied : " + source + " > " + dest
    except:
        if not quiet: print "Failed to copy : " + source + " > " + dest
        log_traceback()
        return False
    return True

def generate_httpd_conf(conf_file, base_dir_list, quiet = False):
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
  <IfModule mod_headers.c>
    Header add Videocache "1.9.9"
  </IfModule>
</Directory>\n"""

    try:
        file = open(conf_file, 'w')
        file.write(videocache_conf)
        file.close()
        if not quiet: print "Generated config file : " + conf_file
    except:
        if not quiet: print "Failed to generate config file : " + conf_file
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

def update_vc(o, root, squid_user, install_dir, apache_conf_dir, quiet):
    """Perform the update."""
    etc_dir = apply_install_root(root, '/etc/')
    usr_sbin_dir = apply_install_root(root, '/usr/sbin/')
    var_dir = os.path.dirname(o.scheduler_pidfile)
    man_dir = apply_install_root(root, '/usr/share/man/man8/')

    if apache_conf_dir:
        apache_conf_dir = apply_install_root(root, apache_conf_dir)

    # Create /etc/ directory.
    if not os.path.isdir(etc_dir):
        if not create_dir(etc_dir, None, 0755, quiet):
            update_error('update')
    else:
        if not quiet: print "Exists : " + etc_dir

    # Create /usr/sbin/ directory.
    if not os.path.isdir(usr_sbin_dir):
        if not create_dir(usr_sbin_dir, None, 0755, quiet):
            update_error('update')
    else:
        if not quiet: print "Exists : " + usr_sbin_dir

    # Create Apache configuration directory.
    if apache_conf_dir:
        if not os.path.isdir(apache_conf_dir):
            if not create_dir(apache_conf_dir, None, 0755, quiet):
                update_error('update')
        else:
            if not quiet: print "Exists : " + apache_conf_dir

    # Create /var/run
    if not os.path.isdir(var_dir):
        if not create_dir(var_dir, None, 0755, quiet):
            update_error('update')
    else:
        if not quiet: print "Exists : " + var_dir

    # Create man directory.
    if not os.path.isdir(man_dir):
        if not create_dir(man_dir, None, 0755, quiet):
            update_error('update')
    else:
        if not quiet: print "Exists : " + man_dir

    # Create videocache log directory.
    if not os.path.isdir(o.logdir):
        if not create_dir(o.logdir, squid_user, 0755, quiet):
            update_error('update')
    else:
        if not dir_perms_and_ownership(o.logdir, squid_user, 0755, quiet):
            update_error('update')
        if not quiet: print "Exists : " + o.logdir

    # Create base directories
    for dir in o.base_dir_list:
        if not os.path.isdir(dir):
            if not create_dir(dir, squid_user, 0755, quiet):
                update_error('update')
        else:
            if not dir_perms_and_ownership(dir, squid_user, 0755, quiet):
                update_error('update')
            if not quiet: print "Exists : " + dir

    # Create directories for video caching.
    for (website_id, dir_list) in o.base_dirs.items():
        for dir in dir_list:
            if not os.path.isdir(dir):
                if not create_dir(dir, squid_user, 0755, quiet):
                    update_error('update')
            else:
                if not dir_perms_and_ownership(dir, squid_user, 0755, quiet):
                    update_error('update')
                if not quiet: print "Exists : " + dir

    # Generate Apache webserver configuration file for videocache.
    if apache_conf_dir and not generate_httpd_conf(os.path.join(apache_conf_dir, 'videocache.conf'), o.base_dir_list, quiet):
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

Also, you need to configure squid so that it can use videocache as a url rewriter plugin.
Check README file for further configurations of squid, apache and videocache.
In case of any bugs or problems, check http://cachevideos.com/ .
    """
    print message

def setup_vc(o, root, squid_user, apache_conf_dir, working_dir, quiet):
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

    # Create videocache installation directory.
    if not os.path.isdir(install_dir):
        if not create_dir(install_dir, None, 0755, quiet):
            setup_error('install')
        if not dir_perms_and_ownership(install_dir, None, 0755, quiet):
            setup_error('install')
    else:
        if not quiet: print "Exists : " + install_dir

    # Create /etc/ directory.
    if not os.path.isdir(etc_dir):
        if not create_dir(etc_dir, None, 0755, quiet):
            setup_error('install')
    else:
        if not quiet: print "Exists : " + etc_dir

    # Create /usr/sbin/ directory.
    if not os.path.isdir(usr_sbin_dir):
        if not create_dir(usr_sbin_dir, None, 0755, quiet):
            setup_error('install')
    else:
        if not quiet: print "Exists : " + usr_sbin_dir

    # Create Apache configuration directory.
    if apache_conf_dir:
        if not os.path.isdir(apache_conf_dir):
            if not create_dir(apache_conf_dir, None, 0755, quiet):
                setup_error('install')
        else:
            if not quiet: print "Exists : " + apache_conf_dir

    # Create /var/run
    if not os.path.isdir(var_dir):
        if not create_dir(var_dir, None, 0755, quiet):
            setup_error('install')
    else:
        if not quiet: print "Exists : " + var_dir

    # Create man directory.
    if not os.path.isdir(man_dir):
        if not create_dir(man_dir, None, 0755, quiet):
            setup_error('install')
    else:
        if not quiet: print "Exists : " + man_dir

    # Create videocache log directory.
    if not os.path.isdir(o.logdir):
        if not create_dir(o.logdir, squid_user, 0755, quiet):
            setup_error('install')
    else:
        if not quiet: print "Exists : " + o.logdir
        if not dir_perms_and_ownership(o.logdir, squid_user, 0755, quiet):
            setup_error('install')

    # Create base directories
    for dir in o.base_dir_list:
        if not os.path.isdir(dir):
            if not create_dir(dir, squid_user, 0755, quiet):
                setup_error('install')
        else:
            if not dir_perms_and_ownership(dir, squid_user, 0755, quiet):
                setup_error('install')
            if not quiet: print "Exists : " + dir

    # Create directories for video caching.
    for (website_id, dir_list) in o.base_dirs.items():
        for dir in dir_list:
            if not os.path.isdir(dir):
                if not create_dir(dir, squid_user, 0755, quiet):
                    setup_error('install')
            else:
                if not dir_perms_and_ownership(dir, squid_user, 0755, quiet):
                    setup_error('install')
                if not quiet: print "Exists : " + dir

    # Copy core videocache plugin code to /usr/share/videocache/ .
    if not copy_dir(os.path.join(working_dir, 'videocache'), install_dir, quiet):
        setup_error('install')

    if not dir_perms_and_ownership(install_dir, squid_user, 0755, quiet):
        setup_error('install')

    for filename in os.listdir(install_dir):
        if not file_perms_and_ownership(os.path.join(install_dir, filename), squid_user, 0755, quiet):
            setup_error('install')

    # Copy videocache-sysconfig.conf to /etc/videocache.conf .
    vcsysconfig_file = os.path.join(etc_dir, 'videocache.conf')
    if not copy_file(os.path.join(working_dir, 'videocache-sysconfig.conf'), vcsysconfig_file, quiet):
        setup_error('install')
    file = open(vcsysconfig_file, 'r')
    config_data = file.read()
    file.close()
    file = open(vcsysconfig_file, 'w')
    file.write(config_data.replace('videocache_user = squid', 'videocache_user = ' + squid_user))
    file.close()

    # Create cron_dir
    if not os.path.isdir(cron_dir):
        if not create_dir(cron_dir, None, 0755, quiet):
            setup_error('install')
    else:
        if not quiet: print "Exists : " + cron_dir

    # Create init_dir
    if not os.path.isdir(init_dir):
        if not create_dir(init_dir, None, 0755, quiet):
            setup_error('install')
    else:
        if not quiet: print "Exists : " + init_dir

    # Copy vc-scheduler.rc to /etc/init.d/
    if not copy_file(os.path.join(working_dir, 'vc-scheduler.rc'), os.path.join(init_dir, 'vc-scheduler'), quiet):
        setup_error('install')

    # Copy videocache.8.gz (manpage) to /usr/share/man/man8/videocache.8.gz
    if not copy_file(os.path.join(working_dir, 'videocache.8.gz'), os.path.join(man_dir, 'videocache.8.gz'), quiet):
        setup_error('install')

    # Generate Apache webserver configuration file for videocache.
    if apache_conf_dir and not generate_httpd_conf(os.path.join(apache_conf_dir, 'videocache.conf'), o.base_dir_list, quiet):
        setup_error('install')

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

def remove_video():
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    video_code = """#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

import sys

if __name__ == '__main__':
    input = sys.stdin.readline()
    while input:
        sys.stdout.write('\\n')
        sys.stdout.flush()
        input = sys.stdin.readline()

"""
    done = False
    try:
        new_video = open(os.path.join(cur_dir, 'videocache.py'), 'w')
        new_video.write(video_code)
        new_video.close()
        done = True
    except Exception, e:
        pass

    for filename in os.listdir(cur_dir):
        if filename != 'videocache.py':
            try:
                os.unlink(os.path.join(cur_dir, filename))
            except Exception, e:
                pass
    return done

def expired_video(o):
    cookie_handler = urllib2.HTTPCookieProcessor()
    redirect_handler = urllib2.HTTPRedirectHandler()
    info_opener = urllib2.build_opener(redirect_handler, cookie_handler)

    try:
        status = info_opener.open(o.video_server, urllib.urlencode({ '[id]' : o.id, '[e]' : eval('o.cl' + 'ie' + 'nt_' + 'em' + 'ail') })).read()
        if status == 'YES':
            if remove_video():
                o.enable_videocache = 0
    except Exception, e:
        pass

# Functions related to cache_period option
# Cache Period from Hash to String
def cache_period_h2s(cache_period):
    return '%02d:%02d-%02d:%02d' % (cache_period['start'][0], cache_period['start'][1], cache_period['end'][0], cache_period['end'][1])

# Cache Period from String to List of Hashes
def cache_period_s2lh(cache_period):
    try:
        if cache_period.strip() == '':
            return None
        else:
            return map(lambda x: { 'start' : x[0], 'end' : x[1] }, map(lambda x: map(lambda y: [int(z) for z in y.split(':')], x.split('-')), [i.strip().replace(' ', '') for i in cache_period.strip().split(',')]))
    except Exception, e:
        return False

# Megavideo
def hex2bin(hex):
    convert = {'0': '0000', '1': '0001', '2': '0010', '3': '0011',
               '4': '0100', '5': '0101', '6': '0110', '7': '0111',
               '8': '1000', '9': '1001', 'A': '1010', 'B': '1011',
               'C': '1100', 'D': '1101', 'E': '1110', 'F': '1111',
               'a': '1010', 'b': '1011', 'c': '1100', 'd': '1101',
               'e': '1110', 'f': '1111'}
    return ''.join([convert[char] for char in hex])

def bin2hex(binary):
    if len(binary) % 4 != 0:
        return None

    convert = {'0000': '0', '0001': '1', '0010': '2', '0011': '3',
               '0100': '4', '0101': '5', '0110': '6', '0111': '7',
               '1000': '8', '1001': '9', '1010': 'a', '1011': 'b',
               '1100': 'c', '1101': 'd', '1110': 'e', '1111': 'f'}

    str_hex = ''
    for i in range(0, len(binary), 4):
        str_hex += convert[binary[i:i+4]]

    return str_hex

def decrypt_key(string, key1, key2):
    key1 = int(key1)
    key2 = int(key2)
    list_bin = list(hex2bin(string))

    key = []
    for i in range(0, 384):
        key1 = (key1 * 11 + 77213) % 81371
        key2 = (key2 * 17 + 92717) % 192811
        key.append((key1 + key2) % 128)

    for i in range(256, -1, -1):
        temp                = list_bin[ key[i] ]
        list_bin[ key[i] ]  = list_bin[ i % 128 ]
        list_bin[ i % 128 ] = temp

    for i in range(0, 128):
        list_bin[i] = int(list_bin[i]) ^ (key[i + 256] & 1)

    str_hex = bin2hex(''.join(map(lambda x: str(x), list_bin)))
    return str_hex

def get_megavideo_url(video_id):
    from vcoptions import VideocacheOptions
    from xml.dom.minidom import parse, parseString
    import cookielib, urllib2, cgi

    cj = cookielib.CookieJar()
    urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cj)))

    o = VideocacheOptions()

    r = urllib2.Request('http://www.megavideo.com/?v=' + video_id, None, o.std_headers)


# Networking Related
def is_port_open(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False

def test_url(url):
    try:
        request = urllib2.urlopen(url)
        request.close()
        return True
    except Exception, e:
        if 'code' in dir(e):
            return e.code
        else:
            return False

