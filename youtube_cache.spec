%define name 	youtube_cache
%define version	0.2
%define release	1
%define prefix	/

Summary: 	Squid redirector to cache Youtube Videos
Name: 		%{name}
Version: 	%{version}
Release: 	%{release}
License: GPL
Group: 		Applications/Internet
URL:      http://fedora.co.in/youtube_cache/
Source:   %{name}-%{version}-%{release}.tar.gz
Buildroot: %{_tmppath}/%{name}-%{version}-%{release}-root 
BuildArch: noarch
Requires: python
Requires:	python-urlgrabber
Requires: squid
Requires: httpd

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
mkdir -p ${RPM_BUILD_ROOT}%{prefix}/etc/sysconfig
mkdir -p ${RPM_BUILD_ROOT}%{prefix}/etc/httpd/conf.d/
mkdir -p ${RPM_BUILD_ROOT}%{prefix}/etc/squid/youtube_cache/
mkdir -p ${RPM_BUILD_ROOT}%{prefix}/var/log/squid/
mkdir -p ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/youtube/temp/
mkdir -p ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/
cp -f youtube_cache/* ${RPM_BUILD_ROOT}%{prefix}/etc/squid/youtube_cache/
cp -f youtube_sysconf.conf ${RPM_BUILD_ROOT}%{prefix}/etc/sysconfig/youtube_cache.conf
cp -f youtube_httpd.conf ${RPM_BUILD_ROOT}%{prefix}/etc/httpd/conf.d/youtube_cache.conf
cp -f youtube_cache.8.gz ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/youtube_cache.8.gz
touch ${RPM_BUILD_ROOT}%{prefix}/var/log/squid/youtube_cache.log

%clean
rm -rf $RPM_BUILD_ROOT
rm -rf $RPM_BUILD_DIR/%{name}-%{version}-%{release}

%files
%{prefix}/etc/squid/youtube_cache/*
%{prefix}/etc/sysconfig/youtube_cache.conf
%{prefix}/etc/httpd/conf.d/youtube_cache.conf
%{prefix}/var/log/squid/youtube_cache.log
%{prefix}/var/spool/squid/youtube/*
%{prefix}/usr/share/man/man8/youtube_cache.8.gz

%post
chown squid:squid ${RPM_BUILD_ROOT}%{prefix}/var/log/squid/youtube_cache.log
chown -R squid:squid ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/youtube
chmod -R 755 ${RPM_BUILD_ROOT}%{prefix}/var/spool/squid/youtube
echo "Reloading httpd service..."
service httpd reload
echo "You need to modify /etc/sysconfig/youtube_cache.conf to make caching work properly."
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
