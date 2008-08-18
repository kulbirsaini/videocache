%define prefix	/

Name:       youtube_cache
Version:    0.3
Release:    1
Summary:    Squid redirector to cache Youtube Videos
License:    GPL
Group:      Applications/Internet
URL:        http://fedora.co.in/youtube_cache/
Source:     %{name}-%{version}-%{release}.tar.gz
Buildroot:  %{_tmppath}/%{name}-%{version}-%{release}-root 
BuildArch:  noarch
Requires:   python
Requires:   python-urlgrabber
Requires:   python-iniparse
Requires:   squid

%description
youtube_cache is a squid redirecto plugin written in Python to facilitate
youtube video caching. It can cache youtube videos in a separate directory
(other than squid cache) in a browsable fashion and can serve the subsequent
requests from the cache. It helps in saving bandwidth and loading time.

%prep

%setup -n %{name}-%{version}-%{release}

%build
echo "No building... its python..." > /dev/null

%install
rm -rf $RPM_BUILD_ROOT/
mkdir -p $RPM_BUILD_ROOT
install -m 755 -d  ${RPM_BUILD_ROOT}%{prefix}/etc/squid/youtube_cache/
install -m 700 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/log/squid/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/youtube/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/youtube/temp/
install -m 744 -d ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/
install -m 644 youtube_cache/* -t ${RPM_BUILD_ROOT}%{prefix}/etc/squid/youtube_cache/
install -m 644 youtube_cache.conf -T ${RPM_BUILD_ROOT}%{prefix}/etc/youtube_cache.conf
install -m 644 youtube_cache.8.gz -T ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/youtube_cache.8.gz
touch ${RPM_BUILD_ROOT}%{prefix}/var/log/squid/youtube_cache.log

%clean
rm -rf $RPM_BUILD_ROOT
rm -rf $RPM_BUILD_DIR/%{name}-%{version}-%{release}

%files
%{prefix}/etc/squid/youtube_cache/*
%{prefix}/etc/youtube_cache.conf
%{prefix}/var/log/squid/youtube_cache.log
%{prefix}/var/spool/squid/youtube/*
%{prefix}/usr/share/man/man8/youtube_cache.8.gz

%post
chown squid:squid ${RPM_BUILD_ROOT}%{prefix}/var/log/squid/youtube_cache.log
chown -R squid:squid ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/youtube
chmod -R 755 ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/youtube
echo "You need to modify /etc/youtube_cache.conf to make caching work properly."
echo "Also you need to configure squid. Check youtube_cache manpage for more details."

%preun

%changelog
* Mon Jun 23 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- 0.2-1
- Fixed few bugs. Added config file support. Now videos are not checked for updates assuming that videos will never change.
- Previously youtube_cache tried to connect to internet directly. Now it uses the proxy on which its hosted.

* Thu Jun 12 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
- 0.1-1
- Initial Version: youtube_cache-0.1 . Works well with squid-2.6STABLE16 and up. Redundand caching.
