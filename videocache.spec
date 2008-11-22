%define prefix	/

Name:       videocache
Version:    1.6
Release:    1
Summary:    videocache is a squid url rewriter plugin to cache Youtube, Metacafe, Dailymotion, Google, Vimeo, Redtube, Xtube, Youporn and MSN Soapbox Videos and Wrzuta.pl audio.
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
videocache is a squid url rewriter plugin written in Python to facilitate youtube, metacafe, dailymotion, google, vimeo, redtube, xtube, youporn and msn soapbox videos and wrzuta.pl audio caching. It can cache videos from various websites in a separate directory (other than squid cache) in a browsable fashion and can serve the subsequentrequests from the cache. It helps in saving bandwidth and loading time.

%prep
%setup -n %{name}-%{version}

%build
echo "No building... its python..." > /dev/null

%pre
# Migrate old caching directories to new one.
if [[ -d %{prefix}/var/spool/squid/video_cache ]] && ! ([[ -d %{prefix}/var/spool/videocache ]]); then
  mv %{prefix}/var/spool/squid/video_cache %{prefix}/var/spool/videocache
  chown -R squid:squid %{prefix}/var/spool/videocache
  chmod -R 755 %{prefix}/var/spool/videocache
fi
if [[ -d %{prefix}/var/spool/video_cache ]] && ! ([[ -d %{prefix}/var/spool/videocache ]]); then
  mv %{prefix}/var/spool/video_cache %{prefix}/var/spool/videocache
  chown -R squid:squid %{prefix}/var/spool/videocache
  chmod -R 755 %{prefix}/var/spool/videocache
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
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/tmp/
install -m 644 videocache/* -t ${RPM_BUILD_ROOT}%{prefix}/usr/share/videocache/
install -m 644 videocache-sysconfig.conf -T ${RPM_BUILD_ROOT}%{prefix}/etc/videocache.conf
install -m 644 videocache-httpd.conf -T ${RPM_BUILD_ROOT}%{prefix}/etc/httpd/conf.d/videocache.conf
install -m 644 videocache.8.gz -T ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/videocache.8.gz
install -m 744 update-vc -T ${RPM_BUILD_ROOT}%{prefix}/usr/sbin/update-vc
touch ${RPM_BUILD_ROOT}%{prefix}/var/log/videocache/videocache.log

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

%files
%{prefix}/etc/videocache.conf
%{prefix}/etc/httpd/conf.d/videocache.conf
%{prefix}/usr/share/videocache/
%{prefix}/usr/share/man/man8/videocache.8.gz
%{prefix}/usr/sbin/update-vc
%{prefix}/var/log/videocache/
%{prefix}/var/spool/videocache/

%post
if [[ -d %{prefix}/var/log/videocache/ ]]; then
  chown -R squid:squid %{prefix}/var/log/videocache/
fi
if [[ -d %{prefix}/var/spool/videocache/ ]]; then
  chown -R squid:squid %{prefix}/var/spool/videocache/
  chmod -R 755 %{prefix}/var/spool/videocache/
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
