%define prefix	/

Name:       videocache
Version:    1.9.2
Release:    1
Summary:    videocache is a squid url rewriter plugin to cache Youtube, Metacafe, Dailymotion, Google, Vimeo, Redtube, Xtube, Youporn, MSN Soapbox, Tube8, TV UOL(BR), Blip TV and Break.com Videos and Wrzuta.pl audio.
License:    GPL
Group:      Applications/Internet
URL:        http://cachevideos.com/
Source:     %{name}-%{version}.tar.gz
Buildroot:  %{_tmppath}/%{name}-%{version}-root 
BuildArch:  noarch
Requires:   python
Requires:   python-urlgrabber
Requires:   python-iniparse
Requires:   squid
Requires:   httpd

%description
videocache is a squid url rewriter plugin written in Python to facilitate youtube, metacafe, dailymotion, google, vimeo, redtube, xtube, youporn, msn soapbox, tube8, tvuol.uol.com.br, blip.tv and break.com videos and wrzuta.pl audio caching. It can cache videos from various websites in a separate directory (other than squid cache) in a browsable fashion and can serve the subsequentrequests from the cache. It helps in saving bandwidth and loading time.

%prep
%setup -n %{name}-%{version}

%build
echo "No building... its python..." > /dev/null

%pre
# Migrate old caching directories to new one.
if [[ -d %{prefix}/var/spool/squid/video_cache ]] && ! ([[ -d %{prefix}/var/spool/videocache ]]); then
  mv %{prefix}/var/spool/squid/video_cache %{prefix}/var/spool/videocache
  chown squid:squid %{prefix}/var/spool/videocache
  chown squid:squid %{prefix}/var/spool/videocache/*
  chmod 755 %{prefix}/var/spool/videocache
  chmod 755 %{prefix}/var/spool/videocache/*
fi
if [[ -d %{prefix}/var/spool/video_cache ]] && ! ([[ -d %{prefix}/var/spool/videocache ]]); then
  mv %{prefix}/var/spool/video_cache %{prefix}/var/spool/videocache
  chown squid:squid %{prefix}/var/spool/videocache
  chown squid:squid %{prefix}/var/spool/videocache/*
  chmod 755 %{prefix}/var/spool/videocache
  chmod 755 %{prefix}/var/spool/videocache/*
fi

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT
install -m 755 -d ${RPM_BUILD_ROOT}%{prefix}/etc/
install -m 755 -d ${RPM_BUILD_ROOT}%{prefix}/etc/httpd/conf.d/
install -m 755 -d ${RPM_BUILD_ROOT}%{prefix}/usr/share/videocache/
install -m 744 -d ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/
install -m 744 -d ${RPM_BUILD_ROOT}%{prefix}/usr/sbin/
install -m 744 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/log/videocache/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/youtube/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/metacafe/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/dailymotion/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/google/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/vimeo/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/redtube/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/xtube/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/wrzuta/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/youporn/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/soapbox/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/tube8/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/tvuol/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/bliptv/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/break/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/tmp/
install -m 644 videocache/* -t ${RPM_BUILD_ROOT}%{prefix}/usr/share/videocache/
install -m 644 videocache-sysconfig.conf -T ${RPM_BUILD_ROOT}%{prefix}/etc/videocache.conf
install -m 644 videocache-httpd.conf -T ${RPM_BUILD_ROOT}%{prefix}/etc/httpd/conf.d/videocache.conf
install -m 644 videocache.8.gz -T ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/videocache.8.gz
install -m 744 update-vc -T ${RPM_BUILD_ROOT}%{prefix}/usr/sbin/update-vc
install -m 744 scripts/vccleaner -T ${RPM_BUILD_ROOT}%{prefix}/usr/sbin/vccleaner
touch ${RPM_BUILD_ROOT}%{prefix}/var/log/videocache/videocache.log

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

%files
%{prefix}/etc/videocache.conf
%{prefix}/etc/httpd/conf.d/videocache.conf
%{prefix}/usr/share/videocache/
%{prefix}/usr/share/man/man8/videocache.8.gz
%{prefix}/usr/sbin/update-vc
%{prefix}/usr/sbin/vccleaner
%{prefix}/var/log/videocache/
%{prefix}/var/spool/videocache/

%post
if [[ -d %{prefix}/var/log/videocache/ ]]; then
  chown squid:squid %{prefix}/var/log/videocache/
  chown squid:squid %{prefix}/var/log/videocache/*
fi
if [[ -d %{prefix}/var/spool/videocache/ ]]; then
  chown squid:squid %{prefix}/var/spool/videocache/
  chown squid:squid %{prefix}/var/spool/videocache/*
  chmod 755 %{prefix}/var/spool/videocache/
  chmod 755 %{prefix}/var/spool/videocache/*
fi
echo "You need to modify /etc/videocache.conf to make caching work properly."
echo "Also you need to configure squid. Check videocache manpage for more details."
echo "Check http://cachevideos.com/ in case of any problems."

%preun
if [[ -d %{prefix}/var/spool/videocache ]];then
  mv %{prefix}/var/spool/videocache ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache1
fi

%postun
if [[ -d %{prefix}/var/spool/videocache1 ]]; then
  mv %{prefix}/var/spool/videocache1 ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache
fi

%changelog
* Mon Mar 9 2009 <kulbirsaini@students.iiit.ac.in>
Entire plugin has been restructured.
Base plugin is now totally separate from the downloading/caching process which will facilitate enhanced performance.
Disk size calculation will no more hang up the plugin.
Directory size is not calculated before every download now.
The calculated size of the cache directories is cached for next 50 downloads.
The caching mechanism is not based on time because cache size will not increase unless there is a download.
The cached directory size stays with XMLRPC server.
The size calculation is done in a forked daemon so that the normal plugin behavior is not affected.
Cache size calculator function is also made generic. Earlier it used to work for 2 level deep directories.
VideoIDPool class is revised to remove unnecessary functions.
'start' and 'begin' parameters are dropped from url while downloading for caching.
Logfiles are rotated properly now. Logfile rotation doesn't require restarting squid.

* Fri Feb 20 2009 <kulbirsaini@students.iiit.ac.in>
If there is only one cache directory, apache alias will be /videocache instead of /videocache/0 .
Added option disk_avail_threshold to check disk full scenarios.
Now size of individual cache directories can be specified via base_dir option itself.
Removed cache_size option attached with individual website directory to speed up and cleanup things.
Fixed a bug related to cache directory switching. (http://cachevideos.com/forum/post/multiple-caches#comment-523)

* Wed Feb 11 2009 <kulbirsaini@students.iiit.ac.in>
Added support for youtube videos served directly from IP Address(without using domains names).
Added support for tube8 videos for mobile platform.
Fixed log misbehavior bug (http://cachevideos.com/forum/post/confused-log-files).

* Tue Feb 10 2009 <kulbirsaini@students.iiit.ac.in>
Added a cache cleaner script to remove unused videos automatically.
Last modified time of a video is updated whenever its a CACHE_HIT to
help the removal script.

* Sun Feb 1 2009 <kulbirsaini@students.iiit.ac.in>
VideoCache now supports multiple caching directories separated by '|' in configuration file.

* Sat Jan 31 2009 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Few more optimizations for XMLRPC Server. Lets see how this goes.
Bumping to version 1.8 .

* Wed Jan 28 2009 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Cleaned up code at a large scale.
Improved assigment for website specific global variables.
Moved deamon forking from XMLRPC Server to client as it would result in less occupied sockets.
Reduced total number of queries to XMLRPC Server in order to get rid of TIME_WAIT sockets.
Major cleanup for cache_video and squid_part functions.

* Mon Jan 26 2009 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Videos are now downloaded only when requested more than once. Option can be customized.

* Sun Jan 25 2009 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Updated to cache tube8.com, tvuol.uol.com.br, blip.tv and break.com videos (including High Quality Videos).
Merged Google and Youtube videos.
Broaden the domains of google/youtube domains for video caching.
Optimized communcation between XMLRPC client and server to minimize the sockets left in TIME_WAIT state.
Extended SimpleXMLRPCServer class to add socket options and shutdown hangle to server.
Additional exception handling at every step.

* Sun Dec 14 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Fixed Bug : http://cachevideos.com/forum/post/cache-directory-size-limiting-checked-only-video-queued .

* Sun Dec 14 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Added extensive exception handling for XMLRPC Server.

* Sat Nov 29 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
videocache.log is not created at installation time when using setup.py .
It is wrong according to debian packaging policy to create empty files at installation time.

* Tue Nov 25 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Extended support for Dailymotion videos served via Content Delivery Networks.
Improved logging.
In case connection breaks, incomplete videos will remain in tmp folder.

* Sun Nov 23 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Fixed setup and update script to finally work with --home or --prefix or --install-root options.
Fixed videocache script to write videos are 0644 and not 0755.
Updated spec file to change permissions of folders only and not recursively.

* Sat Nov 22 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Plugin renamed from youtube_cache to videocache as videocache is more expressive name
and the plugin cache not just youtube but other websites as well.
Complete plugin rebase again to suite python and debian naming/packaging conventions.
New plugin structure
-----------------------------------------------------------------
/etc/videocache.conf # Global config file
/etc/httpd/conf.d/videocache.conf # Apache config file [Red Hat]
/etc/apache2/conf.d/videocache.conf # Apache config file [Debian]
/usr/share/videocache/ # Core plugin code
/usr/share/man/man8/videocache.8.gz # Man Page
/usr/sbin/update-vc # Update file
/var/spool/videocache/ # Cache directories
/var/log/videocache/ # Logging directories
-----------------------------------------------------------------
No symbolik links as they are considered bad according to packaging guidelines.
Squid acls revised.
OptionParser added to setup and update scripts.
Now --home or --prefix or --install-root option can be used while installing and updating videocache.
setup and update scripts' code is documented properly using comments.
Another option enable_video_cache added to config file to control overall caching of all the websites.
videocache.py revised to log more sensible messages. Fixed bug which was reporting false url parser errors.

* Thu Nov 20 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Rebased the entire plugin. Everything moved out of squid directories.
The core plugin code now resides in /usr/share/youtube_cache/ .
The logfiles are now in /var/log/youtube_cache/ directory.
The caching directories are now in /var/spool/video_cache/ directory.
Moved youtube_cache_sysconfig.conf to youtube_cache/youtube_cache.conf .
/etc/youtube_cache.conf will now be a symlink to /usr/share/youtube_cache/youtube_cache.conf .
logfile is not an option anymore. Instead logdir is used now.
Corrected and updated INSTALL/Readme/Manpage files.
Setup file configured to make the transition for caching directories.
Corrected spec file. Uninstalling rpm will not delete cached files.

* Wed Nov 19 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Added critical lines missing from INSTALL/Readme/Manpage.

* Wed Nov 19 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Manpage generation using Text2Tags ( http://txt2tags.sourceforge.net/ ).
Manpage will be delivered uncompressed.

* Tue Nov 18 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Added support for soapbox.msn.com video caching.
Fixed bug with download scheduler. Scheduler was not scheduling more than one video at a time.
Added CHANGELOG file.

* Thu Nov 13 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Youtube Cache updated to cache videos from http://youporn.com/ .

* Wed Nov 13 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Fixed logging error with wrzuta.pl .
Bumped to version 1.3 .

* Wed Nov 12 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Fixed problem with setup.py to copy update-yc to /usr/sbin/ .
Fixed spec file to create /usr/sbin/ .

* Tue Nov 4 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Updated to cache Youtube videos served from googlevideo.com servers.
Updated to cache audio from wrzuta.pl .
Setup new website for youtube cache at http://cachevideos.com/ .
Removed md5 module dependency completely.

* Fri Oct 31 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Fixed serious mistake in squid.conf for youtube_cache.

* Fri Oct 31 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Updated spec file.
Bumped to version 1.1 .

* Fri Oct 31 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Improved INSTALL and Readme files.
Improved video id detection for youtube and google videos.
Removed python 2.5 dependency. Now works with python 2.4.
Sanitized the reloading system while squid reloads.

* Thu Oct 30 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Added setup file for automating youtube_cache installation.
Fixed loads of bugs generated due to forking daemons.
All external processes except downloader are now started as threads.
Processes and threads are immedietely killed whenever squid is reloaded or restarted.
No backtracing goes to cache.log now.

* Fri Oct 24 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Fixes for crashes by adding try-except statements.
A bit of performance enhancement by avoiding md5 hashes for video ids.

* Fri Oct 24 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Implemented bandwidth management.
User can put cap on max parallel downloads of videos
so that entire banwidth is not consumed in caching.

* Fri Oct 17 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Updated spec file.
Bumped to version 0.9.

* Fri Oct 17 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Implemented caching for Vimeo.com HD videos.
Fixed INSTALL/Readme/manpage file for version 0.8.

* Sun Oct 12 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Updated spec file.
Bumped to version 0.8

* Sun Oct 12 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Implemented video caching for redtube.com and xtube.com .
Renovated manpage and config file.
Updated INSTALL/Readme files.

* Sat Oct 11 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Updated spec file.
Bumped to version 0.7

* Sat Oct 11 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Clients access the video files are logged for statistics.
Logfile size introduced to control logging.
Logrotate facility for rotating logfiles added.
Added video file size to logging for statistics.
Whenever cache is full, warning will be logged now.
Bug fix : If cache is full, the videos from cache will be served.
Previously, the plugin used to exit if the cache was full.

* Tue Oct 7 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Google Video caching implemented. Need to update spec/INSTALL/Readme/manpage files.

* Tue Oct 7 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Updated spec file.

* Tue Oct 7 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Implemented caching for yet another video site dailymotion.com. 
Working absolutely fine. Bumped to version 0.6.

* Sat Oct 4 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Updated INSTALL/Readme/Spec/manpage files.
Bumped to version 0.5 .

* Sat Oct 4 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Implemented Metacafe.com video caching. Need to update INSTALL and spec file.

* Sat Oct 4 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
Implemented Metacafe.com video caching. Need to update INSTALL and spec file.

* Tue Sep 30 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
Fixed bugs related to large video files. Implemened all the options related
to video size. Removed python bases webserver as it was creating problems in
seeking in large video files. Added httpd dependency again. Now XMLRPC will
be used for communcations among forked daemons. Added support for proxy
authentication.

* Sun Aug 24 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
A new set of configuration options. Not implemented yet. On TODO list.

* Tue Aug 19 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
Removed apache dependency. Now python web-server is used for serving videos. Fixed few bugs.

* Wed Jun 25 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
Modified config and Readme files. Added INSTALL file.

* Tue Jun 24 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
Added Readme file again.

* Mon Jun 23 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
Bumped to 0.2 . Fixed some more bugs. Added spec file to generate rpms for fedora :)

* Mon Jun 23 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
Hierarchy rearranged.

* Mon Jun 23 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
0.2-1
Fixed few bugs. Added config file support. Now videos are not checked for updates assuming that videos will never change.
Previously youtube_cache tried to connect to internet directly. Now it uses the proxy on which its hosted.

* Thu Jun 12 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
0.1-1
Initial Version: youtube_cache-0.1 . Works well with squid-2.6STABLE16 and up. Redundand caching.
