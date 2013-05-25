#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import os
import pwd
import shutil
import stat

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

# Read/Write/eXecute flags for a path
def is_readable(path):
    uid = os.getuid()
    euid = os.geteuid()
    gid = os.getgid()
    egid = os.getegid()

    if uid == euid and gid == egid:
        return os.access(path, os.R_OK)

    st = os.stat(path)
    if st.st_uid == euid:
        return st.st_mode & stat.S_IRUSR != 0

    groups = os.getgroups()
    if st.st_gid == egid or st.st_gid in groups:
        return st.st_mode & stat.S_IRGRP != 0

    return st.st_mode & stat.S_IROTH != 0

def is_writable(path):
    uid = os.getuid()
    euid = os.geteuid()
    gid = os.getgid()
    egid = os.getegid()

    if uid == euid and gid == egid:
        return os.access(path, os.W_OK)

    st = os.stat(path)
    if st.st_uid == euid:
        return st.st_mode & stat.S_IWUSR != 0

    groups = os.getgroups()
    if st.st_gid == egid or st.st_gid in groups:
        return st.st_mode & stat.S_IWGRP != 0

    return st.st_mode & stat.S_IWOTH != 0

def is_executable(path):
    uid = os.getuid()
    euid = os.geteuid()
    gid = os.getgid()
    egid = os.getegid()

    if uid == euid and gid == egid:
        return os.access(path, os.X_OK)

    st = os.stat(path)
    if st.st_uid == euid:
        return st.st_mode & stat.S_IXUSR != 0

    groups = os.getgroups()
    if st.st_gid == egid or st.st_gid in groups:
        return st.st_mode & stat.S_IXGRP != 0

    return st.st_mode & stat.S_IXOTH != 0

# Create/Copy/Move directories and files
def set_permissions(dir, mode=0755, quiet = True):
    """Change the permissions of a directory."""
    try:
        os.chmod(dir, mode)
        return True
    except Exception, e:
        if not quiet: print "Failed to change permission : " + dir
        return False

def set_ownership(dir, user=None, quiet = True):
    """Change the ownership of a directory."""
    if user == None:
        if not quiet: print "User not specified."
        return True

    try:
        user = pwd.getpwnam(user)
    except KeyError, e:
        if not quiet: print "User " + user + " doesn't exist."
        return False
    except Exception, e:
        if not quiet: print "Could not get user ID."
        return False

    try:
        stats = os.stat(dir)
        if stats is not None and stats[stat.ST_UID] == user.pw_uid and stats[stat.ST_GID] == user.pw_gid:
            if not quiet: print "User is already the owner."
            return True
    except Exception, e:
        pass

    try:
        os.chown(dir, user.pw_uid, user.pw_gid)
        if not quiet: print "Ownership changed : " + dir
        return True
    except Exception, e:
        if not quiet: print "Failed to change ownership : " + dir
        return False

def set_permissions_and_ownership(path, user = None, mode = 0755, quiet = True):
    if not set_permissions(path, mode, quiet): return False
    if not set_ownership(path, user, quiet): return False
    return True

def create_file(filename, user=None, mode=0755, quiet = True):
    """Create a file in the filesystem with user:group ownership and mode as permissions."""
    try:
        file(filename, 'a').close()
        if not quiet: print "Created : " + filename
    except Exception, e:
        if not quiet: print "Failed to create : " + filename
        return False
    
    return set_permissions_and_ownership(filename, user, mode, quiet)

def create_dir(dir, user=None, mode=0755, quiet = True):
    """Create a directory in the filesystem with user:group ownership and mode as permissions."""
    try:
        os.makedirs(dir, mode)
        if not quiet: print "Created : " + dir
    except Exception, e:
        if not quiet: print "Failed to create : " + dir
        return False

    return set_permissions_and_ownership(dir, user, mode, quiet)

def create_or_update_dir(dir, user = None, mode = 0755, quiet = True):
    if os.path.isdir(dir): return set_permissions_and_ownership(dir, user, mode, quiet)
    if not create_dir(dir, user, mode, quiet): return False
    return True

def copy_file(source, dest, quiet = True):
    """Copies the source file to dest file."""
    try:
        shutil.copy2(source, dest)
        if not quiet: print "Copied : " + source + " > " + dest
        return True
    except Exception, e:
        if not quiet: print "Failed to copy : " + source + " > " + dest
        return False

def copy_dir(source, dest, quiet = True):
    """Copies the source directory recursively to dest dir."""
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
            if not quiet: print "Removed existing : " + dest
    except Exception, e:
        if not quiet: print "Failed to remove existing : " + dest
        return False

    try:
        shutil.copytree(source, dest)
        if not quiet: print "Copied : " + source + " > " + dest
        return True
    except:
        if not quiet: print "Failed to copy : " + source + " > " + dest
        return False

def move_file(source_file, target_file):
    """Moves file from source_file to target_file."""
    try:
        shutil.move(source_file, target_file)
        return True
    except:
        return False

def remove_file(target_file):
    try:
        if os.path.isfile(target_file): os.unlink(target_file)
        return True
    except:
        return False

