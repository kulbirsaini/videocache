#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from common import *
from error_codes import *

import atexit
import errno
import os
import signal
import sys
import time

class VideocacheDaemon:

    def __init__(self, pidfile = '/dev/null', **kwargs):
        self.pidfile = pidfile
        self.stdin = kwargs.get('stdin', open('/dev/null', 'r'))
        self.stdout = kwargs.get('stdout', open('/dev/null', 'a+'))
        self.stderr = kwargs.get('stderr', open('/dev/null', 'a+', 0))
        self.uid = kwargs.get('uid', 0)
        self.name = kwargs.get('name', 'Process')

    def daemonize(self):
        pid = os.fork()
        if pid > 0:
            sys.exit(0)

        os.chdir("/")
        os.setsid()
        os.umask(0)

        pid = os.fork()
        if pid > 0:
            sys.exit(0)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        os.dup2(self.stdin.fileno(), sys.stdin.fileno())
        os.dup2(self.stdout.fileno(), sys.stdout.fileno())
        os.dup2(self.stderr.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delete_pidfile)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)
        os.setgid(self.uid)
        os.setuid(self.uid)

    def delete_pidfile(self):
        if os.path.isfile(self.pidfile):
            os.remove(self.pidfile)

    def start(self):
        # Check for a pidfile to see if the daemon already running
        try:
            pid = int(file(self.pidfile,'r').read().strip())
        except Exception, e:
            pid = None

        if pid:
            status = is_running(pid)
            if status == None:
                status = proc_test(pid)

            if status == True:
                message = 'Pidfile exists and ' + self.name + ' is already running with process id: ' + str(pid) + '.'
                sys.stdout.write(message + '\n')
            elif status == False:
                message = 'Pidfile exists but ' + self.name + ' is not running.'
                sys.stderr.write(message + '\n')
            else:
                message = 'Pidfile exists but could not determine the status of ' + self.name + ' with process id: ' + str(pid) + '.'
                sys.stderr.write(message + '\n')

            sys.exit(1)

        sys.stdout.write(self.name + ' started.\n')
        sys.stdout.flush()
        sys.stderr.flush()
        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        # Get the pid from the pidfile
        try:
            pid = int(file(self.pidfile,'r').read().strip())
        except Exception, e:
            pid = None

        if not pid:
            message = 'Pidfile ' + self.pidfile + ' does not exist. ' + self.name + ' may not be running.'
            sys.stderr.write(message + '\n')
            return # not an error in a restart

        # Try killing the daemon process	
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError, e:
            if e.errno == errno.ESRCH:
                message = self.name + ' was not running.'
                status = False
            elif e.errno == errno.EPERM:
                message = 'Operation not permitted. Could not send a Terminate signal to ' + self.name + ' with process id: ' + str(pid) + '.'
                status = None
        else:
            message = self.name + ' stopped.'
            status = True
        if status == None:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError, e:
                if e.errno == errno.ESRCH:
                    message = self.name + ' was not running.'
                    status = False
                elif e.errno == errno.EPERM:
                    message = 'Operation not permitted. Could not send a KILL signal to ' + self.name + ' with process id: ' + str(pid) + '.'
                    status = None
            else:
                message = self.name + ' stopped.'
                status = True

        if status == True:
            sys.stdout.write(message + '\n')
        else:
            sys.stderr.write(message + '\n')

        if status != None and os.path.exists(self.pidfile):
            os.remove(self.pidfile)
        if status == None: sys.exit(1)
        sys.stdout.flush()
        sys.stderr.flush()

    def reload(self):
        # Check for a pidfile to see if the daemon already running
        try:
            pid = int(file(self.pidfile,'r').read().strip())
        except Exception, e:
            pid = None

        status = False
        if pid:
            message = 'Unknown error occured.'
            try:
                os.kill(pid, signal.SIGUSR1)
            except OSError, e:
                if e.errno == errno.ESRCH:
                    message = self.name + ' not running.'
                elif e.errno == errno.EPERM:
                    message = 'Could not signal ' + self.name + '. Permission denied'
            else:
                message = 'Reloading ' + self.name + '.'
                status = True
        else:
            message = 'Could not get ' + self.name + ' id from pidfile at ' + self.pidfile + '.'

        if status:
            sys.stdout.write(message + '\n')
        else:
            sys.stderr.write(message + '\n')
        sys.stdout.flush()
        sys.stderr.flush()

    def restart(self):
        self.stop()
        self.start()

    def status(self):
        # Check for a pidfile to see if the daemon already running
        try:
            pid = int(file(self.pidfile,'r').read().strip())
        except Exception, e:
            pid = None

        if pid:
            status = is_running(pid)
            if status == None:
                status = proc_test(pid)

            if status == True:
                message = self.name + ' is running with process id: ' + str(pid) + '.'
                sys.stdout.write(message + '\n')
            elif status == False:
                message = self.name + ' is not running.'
                sys.stderr.write(message + '\n')
            else:
                message = 'Could not determine the status of ' + self.name + ' with process id: ' + str(pid) + '.'
                sys.stderr.write(message + '\n')
        else:
            message = 'Could not determine the status of ' + self.name + '. Pidfile does not exist.'
            sys.stderr.write(message + '\n')



    def run(self):
        pass

