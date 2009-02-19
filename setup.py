#!/usr/bin/env python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# (C) Copyright 2008-2009 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
#
# For more information check http://cachevideos.com/
#


from videocache.config import readMainConfig, readStartupConfig
from optparse import OptionParser
import logging
import logging.handlers
import os
import pwd
import shutil
import sys

# The user which runs the squid proxy server or daemon. Change this according to your system.
squid_user = 'squid'
# The group which runs the squid proxy server or daemon. Change this according to your system.
squid_group = 'squid'
# The location of videocache installation directory. You don't need to change this.
install_dir = '/usr/share/'
# The directory to store application specific configuration files for Apache Web Server. Change this according to your system.
# For Red Hat and derivatives, you don't need to change this.
# For Debian and derivatives its normally /etc/apache2/conf.d/
apache_conf_dir = '/etc/httpd/conf.d/'
# The directory to store man pages.
man_dir = '/usr/share/man/man8/'
# The user specific directory to have exectuables.
usr_sbin_dir = '/usr/sbin/'
# The directory to store system level configuration files.
etc_dir = '/etc'

def set_logging(logfile):
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename=logfile,
                        filemode='w')
    return logging.info

def create_dir(dir, user=None, group=None, mode=0755):
    """Create a directory in the filesystem with user:group ownership and mode as permissions."""
    try:
        os.makedirs(dir, mode)
        log(format%("Created directory " + dir + " ."))
    except:
        log(format%("Could not create directory " + dir + " ."))
        return False
    return dir_perms_and_ownership(dir, user, group, mode)

def dir_perms_and_ownership(dir, user=None, group=None, mode=0755):
    """Change the permissions and ownership of a directory."""
    try:
        os.chmod(dir, mode)
    except:
        log(format%("Could not change permissions of directory " + dir + " ."))

    if user == None:
        return True

    user = pwd.getpwnam(user)[2]
    if group != None:
        group = pwd.getpwnam(group)[3]
    else:
        group = user

    try:
        os.chown(dir, user, group)
        log(format%("Changed ownership of " + dir + " ."))
    except:
        log(format%("Could not change ownership of directory " + dir + " ."))
        return False

    return True

def create_file(filename, user=None, group=None, mode=0755):
    """Create a file in the filesystem with user:group ownership and mode as permissions."""
    try:
        file = open(filename, 'a')
        file.close()
        log(format%("Created file " + filename + " ."))
    except:
        log(format%("Could not create file " + filename + " ."))
        return False
    
    try:
        os.chmod(filename, mode)
        log(format%("Changed mode of file " + filename + " ."))
    except:
        log(format%("Could not change the mode of the file " + filename + " ."))
        return False

    if user == None:
        return True

    user = pwd.getpwnam(user)[2]
    if group != None:
        group = pwd.getpwnam(group)[3]
    else:
        group = user

    try:
        os.chown(filename, user, group)
        log(format%("Changed ownership of file " + filename + " ."))
    except:
        log(format%("Could not change ownership of file " + filename + " ."))
        return False
    return True

def copy_file(source, dest):
    """Copies the source file to dest file."""
    try:
        shutil.copy2(source, dest)
        log(format%("Copied file " + source + " to " + dest + " ."))
    except:
        log(format%("Could not copy the file " + source + " to file " + dest + " ."))
        return False
    return True

def copy_dir(source, dest):
    """Copies the source directory recursively to dest dir."""
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
            log(format%("Removed already existing directory " + dest + " ."))
    except:
        log(format%("Could not remove the already existing destination directory " + dest + " ."))
        return False
    try:
        shutil.copytree(source, dest)
        log(format%("Copied source directory " + source + " to " + dest + " ."))
    except:
        log(format%("Could not copy directory " + source + " to " + dest + " ."))
        return False
    return True

def generate_httpd_conf(conf_file, base_dir):
    """Generates /etc/httpd/conf.d/videocache.conf for apache web server for serving videos."""
    videocache_conf = """##############################################################################
#                                                                            #
# file : """ + conf_file + " "*(68 - len(conf_file)) + """#
#                                                                            #
# videocache is a squid url rewriter to cache videos from various websites.  #
# Check http://cachevideos.com/ for more details.                            #
#                                                                            #
# ----------------------------- Note This ---------------------------------- #
# Don't change this file unless you have good knowledge of how Apache works. #
# Don't forget to reload httpd and squid services if you change this file.   #
#                                                                            #
##############################################################################\n\n"""
    for dir in base_dir:
        if len(base_dir) == 1:
            videocache_conf += "Alias /videocache " + dir
        else:
            videocache_conf += "Alias /videocache/" + str(base_dir.index(dir)) + " " + dir

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
        log(format%("Generated config file for Apache webserver in file " + conf_file + " ."))
    except:
        log(format%("Could not write config file for apache web server to " + conf_file + " ."))
        return False
    return True

def error(error_code):
    """Report error while updating/installing videocache with proper error code."""
    help_message =  """
Usage: python setup.py install (as root/super user)
Please see http://cachevideos.com/installation for more information or getting help.
    """
    install_error =  """
An error has occured while installing videocache.
Please check videocache-setup.log for more details.
Please see http://cachevideos.com/installation for more information or getting help.
    """
    uid_error = """
You must be root to setup/install videocache.
Please see http://cachevideos.com/installation for more information or getting help.
    """
    if error_code == INSTALL_ERROR:
        print install_error
        sys.exit(error_code)
    if error_code == UID_ERROR:
        print uid_error
        sys.exit(UID_ERROR)
    if error_code == USAGE_ERROR:
        print help_message
        sys.exit(USAGE_ERROR)
    return

def success():
    """Print informative messages after successfull installation."""
    message = """
videocache setup has completed successfully.
Now you must reload httpd service on your machine by using the following command
[root@localhost ~]# service httpd reload [ENTER]
Also, you need to configure squid so that it can use videocache as a url rewritor plugin.
Check README file for further configurations of squid, httpd and videocache.
In case of any bugs or problems, check http://cachevideos.com/ .
    """
    print message

def setup(root):
    """Perform the setup."""
    global base_dir, squid_user, squid_group, install_dir, apache_conf_dir, man_dir, usr_sbin_dir, etc_dir, log, logdir, cache_dir_list, old_cache_dirs
    # Create Apache configuration directory.
    if not os.path.isdir(apache_conf_dir):
        if not create_dir(apache_conf_dir):
            error(INSTALL_ERROR)
    else:
        log(format%("Directory " + apache_conf_dir + " already exists."))

    # Create system configuration directory.
    if not os.path.isdir(etc_dir):
        if not create_dir(etc_dir):
            error(INSTALL_ERROR)
    else:
        log(format%("Directory " + etc_dir + " already exists."))

    # Create videocache installation directory.
    if not os.path.isdir(install_dir):
        if not create_dir(install_dir):
            error(INSTALL_ERROR)
    else:
        log(format%("Directory " + install_dir + " already exists."))

    # Create directory to store man page.
    if not os.path.isdir(man_dir):
        if not create_dir(man_dir):
            error(INSTALL_ERROR)
    else:
        log(format%("Directory " + man_dir + " already exists."))

    # Create usr_sbin_dir directory.
    if not os.path.isdir(usr_sbin_dir):
        if not create_dir(usr_sbin_dir):
            error(INSTALL_ERROR)
    else:
        log(format%("Directory " + usr_sbin_dir + " already exists."))

    # Create videocache log directory.
    if not os.path.isdir(logdir):
        if not create_dir(logdir, squid_user, squid_group):
            error(INSTALL_ERROR)
    else:
        log(format%("Directory " + logdir + " already exists."))

    # Migrate older caching directories to new one if install root is /
    """
    if root == '/':
        for dir in old_cache_dirs:
            if os.path.isdir(dir) and not os.path.isdir(base_dir[0]):
                os.rename(dir, base_dir[0])
    """

    # Create directories for video caching.
    for base_path in base_dir:
        for dir in cache_dir_list:
            new_dir = os.path.join(base_path, dir)
            if not os.path.isdir(new_dir):
                if not create_dir(new_dir, squid_user, squid_group):
                    error(INSTALL_ERROR)
            else:
                if not dir_perms_and_ownership(new_dir, squid_user, squid_group):
                    error(INSTALL_ERROR)
                log(format%("Directory " + new_dir + " already exists."))

    # Copy core videocache plugin code to /usr/share/videocache/ .
    if not copy_dir('./videocache/', os.path.join(install_dir, 'videocache')):
        error(INSTALL_ERROR)

    # Copy videocache-sysconfig.conf to /etc/videocache.conf .
    if not copy_file('./videocache-sysconfig.conf', os.path.join(etc_dir, 'videocache.conf')):
        error(INSTALL_ERROR)

    # Copy vccleaner to /usr/sbin/vccleaner
    if not copy_file('./scripts/vccleaner', os.path.join(usr_sbin_dir, 'vccleaner')):
        error(INSTALL_ERROR)
    os.chmod(os.path.join(usr_sbin_dir, 'vccleaner'),0744)

    # Copy update-vc to /usr/sbin/update-vc
    if not copy_file('./update-vc', os.path.join(usr_sbin_dir, 'update-vc')):
        error(INSTALL_ERROR)
    os.chmod(os.path.join(usr_sbin_dir, 'update-vc'),0744)

    # Copy videocache.8.gz (manpage) to /usr/share/man/man8/videocache.8.gz
    if not copy_file('./videocache.8.gz', os.path.join(man_dir, 'videocache.8.gz')):
        error(INSTALL_ERROR)

    # Generate Apache webserver configuration file for videocache.
    if not generate_httpd_conf(os.path.join(apache_conf_dir, 'videocache.conf'), base_dir):
        error(INSTALL_ERROR)

    success()
    return

def apply_install_root(root, dir):
    """Apply --install-root or --home option to all the directories."""
    return os.path.join(root, dir.strip('/'))

def main(root):
    global base_dir, squid_user, squid_group, install_dir, apache_conf_dir, man_dir, usr_sbin_dir, etc_dir, log, logdir, cache_dir_list, old_cache_dirs
    install_dir = apply_install_root(root, install_dir)
    apache_conf_dir = apply_install_root(root, apache_conf_dir)
    man_dir = apply_install_root(root, man_dir)
    usr_sbin_dir = apply_install_root(root, usr_sbin_dir)
    etc_dir = apply_install_root(root, etc_dir)

    # Read the configure file. FIXME
    mainconf =  readMainConfig(readStartupConfig(config_file, root))

    # Global Options
    base_dir = [apply_install_root(root, dir_tup.split(':')[0].strip()) for dir_tup in mainconf.base_dir.strip().split('|')]
    temp_dir = mainconf.temp_dir
    logdir = apply_install_root(root, mainconf.logdir)

    # Directories for individual websites
    youtube_cache_dir = mainconf.youtube_cache_dir
    metacafe_cache_dir = mainconf.metacafe_cache_dir
    dailymotion_cache_dir = mainconf.dailymotion_cache_dir
    google_cache_dir = mainconf.google_cache_dir
    redtube_cache_dir = mainconf.redtube_cache_dir
    xtube_cache_dir = mainconf.xtube_cache_dir
    vimeo_cache_dir = mainconf.vimeo_cache_dir
    wrzuta_cache_dir = mainconf.wrzuta_cache_dir
    youporn_cache_dir = mainconf.youporn_cache_dir
    soapbox_cache_dir = mainconf.soapbox_cache_dir
    tube8_cache_dir = mainconf.tube8_cache_dir
    tvuol_cache_dir = mainconf.tvuol_cache_dir
    bliptv_cache_dir = mainconf.bliptv_cache_dir
    break_cache_dir = mainconf.break_cache_dir

    # List of cache directories
    cache_dir_list = [temp_dir, youtube_cache_dir, metacafe_cache_dir, dailymotion_cache_dir, google_cache_dir, redtube_cache_dir, xtube_cache_dir, vimeo_cache_dir, wrzuta_cache_dir, youporn_cache_dir, soapbox_cache_dir, tube8_cache_dir, tvuol_cache_dir, bliptv_cache_dir, break_cache_dir]

    # videocache directories in older version
    old_cache_dirs = ['/var/spool/squid/video_cache/', '/var/spool/video_cache']

if __name__ == '__main__':
    # Parse command line options.
    parser = OptionParser()
    parser.add_option('--home')
    parser.add_option('--prefix')
    parser.add_option('--install-root')
    options, args = parser.parse_args()

    # Global Options.
    USAGE_ERROR = 1
    UID_ERROR = 2
    INSTALL_ERROR = 3
    format = '%s'
    # The location of system configuration file for videocache.
    config_file = './videocache-sysconfig.conf'
    # The location of logfile to write setup/install logs.
    setup_logfile = './videocache-setup.log'
    # Set logging.
    log = set_logging(setup_logfile)

    if 'install' in args:
        if os.getuid() != 0:
            log(format%("You must be root to install/setup videocache."))
            error(UID_ERROR)
        else:
            # If --home or --prefix or --install-root option is used, then apply settings.
            root = '/'
            if options.home:
                root = options.home
            if options.prefix:
                root = options.prefix
            if options.install_root:
                root = options.install_root
            main(root)
            setup(root)
            pass
    else:
        error(USAGE_ERROR)
