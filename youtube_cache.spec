%define prefix	/

Name:       youtube_cache
Version:    1.1
Release:    1
Summary:    Squid url rewriter plugin to cache Youtube, Metacafe, Dailymotion, Google, Vimeo, Redtube and Xtube Videos.
License:    GPL
Group:      Applications/Internet
URL:        http://fedora.co.in/youtube_cache/
Source:     %{name}-%{version}.tar.gz
Buildroot:  %{_tmppath}/%{name}-%{version}-root 
BuildArch:  noarch
Requires:   python
Requires:   python-urlgrabber
Requires:   python-iniparse
Requires:   squid
Requires:   httpd

%description
youtube_cache is a squid url rewriter plugin written in Python to facilitate youtube, metacafe, dailymotion, google, vimeo,
redtube and xtube video caching. It can cache youtube/metacafe/dailymotion/google/vimeo/redtube/xtube videos in a
separate directory (other than squid cache) in a browsable fashion and can serve
the subsequentrequests from the cache. It helps in saving bandwidth and loading time.

%prep

%setup -n %{name}-%{version}

%build
echo "No building... its python..." > /dev/null

%install
rm -rf $RPM_BUILD_ROOT/
mkdir -p $RPM_BUILD_ROOT
install -m 755 -d  ${RPM_BUILD_ROOT}%{prefix}/etc/squid/youtube_cache/
install -m 755 -d  ${RPM_BUILD_ROOT}%{prefix}/etc/httpd/conf.d/
install -m 700 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/log/squid/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/video_cache/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/video_cache/youtube/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/video_cache/metacafe/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/video_cache/dailymotion/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/video_cache/google/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/video_cache/vimeo/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/video_cache/redtube/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/video_cache/xtube/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/video_cache/tmp/
install -m 744 -d ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/
install -m 644 youtube_cache/* -t ${RPM_BUILD_ROOT}%{prefix}/etc/squid/youtube_cache/
install -m 644 youtube_cache_sysconfig.conf -T ${RPM_BUILD_ROOT}%{prefix}/etc/youtube_cache.conf
install -m 644 youtube_cache_httpd.conf -T ${RPM_BUILD_ROOT}%{prefix}/etc/httpd/conf.d/youtube_cache.conf
install -m 644 youtube_cache.8.gz -T ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/youtube_cache.8.gz
touch ${RPM_BUILD_ROOT}%{prefix}/var/log/squid/youtube_cache.log

%clean
rm -rf $RPM_BUILD_ROOT
rm -rf $RPM_BUILD_DIR/%{name}-%{version}

%files
%{prefix}/etc/squid/youtube_cache/
%{prefix}/etc/youtube_cache.conf
%{prefix}/etc/httpd/conf.d/youtube_cache.conf
%{prefix}/var/log/squid/youtube_cache.log
%{prefix}/usr/share/man/man8/youtube_cache.8.gz

%post
chown squid:squid ${RPM_BUILD_ROOT}%{prefix}/var/log/squid/youtube_cache.log
chown -R squid:squid ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/video_cache
echo "You need to modify /etc/youtube_cache.conf to make caching work properly."
echo "Also you need to configure squid. Check youtube_cache manpage for more details."
echo "Check http://fedora.co.in/youtube_cache/ in case of any problems."

%preun

%changelog
* Fri Oct 31 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Updated spec file.
- Bumped to version 1.1 .

* Fri Oct 31 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Improved INSTALL and Readme files.
- Improved video id detection for youtube and google videos.
- Removed python 2.5 dependency. Now works with python 2.4.
- Sanitized the reloading system while squid reloads.

* Thu Oct 30 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Added setup file for automating youtube_cache installation.
- Fixed loads of bugs generated due to forking daemons.
- All external processes except downloader are now started as threads.
- Processes and threads are immedietely killed whenever squid is reloaded or restarted.
- No backtracing goes to cache.log now.

* Fri Oct 24 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Fixes for crashes by adding try-except statements.
- A bit of performance enhancement by avoiding md5 hashes for video ids.

* Fri Oct 24 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Implemented bandwidth management.
- User can put cap on max parallel downloads of videos
- so that entire banwidth is not consumed in caching.

* Fri Oct 17 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Updated spec file.
- Bumped to version 0.9.

* Fri Oct 17 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Implemented caching for Vimeo.com HD videos.
- Fixed INSTALL/Readme/manpage file for version 0.8.

* Sun Oct 12 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Updated spec file.
- Bumped to version 0.8

* Sun Oct 12 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Implemented video caching for redtube.com and xtube.com .
- Renovated manpage and config file.
- Updated INSTALL/Readme files.

* Sat Oct 11 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Updated spec file.
- Bumped to version 0.7

* Sat Oct 11 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Clients access the video files are logged for statistics.
- Logfile size introduced to control logging.
- Logrotate facility for rotating logfiles added.
- Added video file size to logging for statistics.
- Whenever cache is full, warning will be logged now.
- Bug fix : If cache is full, the videos from cache will be served.
- Previously, the plugin used to exit if the cache was full.

* Tue Oct 7 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Google Video caching implemented. Need to update spec/INSTALL/Readme/manpage files.

* Tue Oct 7 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Updated spec file.

* Tue Oct 7 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Implemented caching for yet another video site dailymotion.com. 
- Working absolutely fine. Bumped to version 0.6.

* Sat Oct 4 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Updated INSTALL/Readme/Spec/manpage files.
- Bumped to version 0.5 .

* Sat Oct 4 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Implemented Metacafe.com video caching. Need to update INSTALL and spec file.

* Sat Oct 4 2008 Kubir Saini <kulbirsaini@students.iiit.ac.in>
- Implemented Metacafe.com video caching. Need to update INSTALL and spec file.

* Tue Sep 30 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- Fixed bugs related to large video files. Implemened all the options related
- to video size. Removed python bases webserver as it was creating problems in
- seeking in large video files. Added httpd dependency again. Now XMLRPC will
- be used for communcations among forked daemons. Added support for proxy
- authentication.

* Sun Aug 24 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- A new set of configuration options. Not implemented yet. On TODO list.

* Tue Aug 19 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- Removed apache dependency. Now python web-server is used for serving videos. Fixed few bugs.

* Wed Jun 25 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- Modified config and Readme files. Added INSTALL file.

* Tue Jun 24 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- Added Readme file again.

* Mon Jun 23 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- Bumped to 0.2 . Fixed some more bugs. Added spec file to generate rpms for fedora :)

* Mon Jun 23 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- Hierarchy rearranged.

* Mon Jun 23 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- 0.2-1
- Fixed few bugs. Added config file support. Now videos are not checked for updates assuming that videos will never change.
- Previously youtube_cache tried to connect to internet directly. Now it uses the proxy on which its hosted.

* Thu Jun 12 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- 0.1-1
- Initial Version: youtube_cache-0.1 . Works well with squid-2.6STABLE16 and up. Redundand caching.
