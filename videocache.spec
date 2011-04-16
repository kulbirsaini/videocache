%define prefix	/

Name:       videocache
Version:    1.9.8
Release:    1
Summary:    Videocache is a squid url rewriter plugin to cache Youtube, Facebook, Metacafe, Dailymotion, Google, Vimeo, Xhamster, Xvideos, Redtube, Xtube, Youporn, MSN Soapbox, Tube8, Blip TV, Break.com and Wrzuta.pl videos.
License:    Videocache Commercial License
Group:      Applications/Internet
URL:        http://cachevideos.com/
Source:     %{name}-%{version}.tar.gz
Buildroot:  %{_tmppath}/%{name}-%{version}-root 
BuildArch:  noarch
Requires:   python
Requires:   python-iniparse
Requires:   squid
Requires:   httpd

%description
Videocache is a squid url rewriter plugin written in Python to facilitate youtube, facebook, metacafe, dailymotion, google, vimeo, xhamster, xvideos, redtube, xtube, youporn, msn soapbox, tube8, blip.tv, break.com and wrzuta.pl video caching. It can cache videos from various websites in a separate directory (other than squid cache directory) in a browsable fashion and can serve the subsequentrequests from the cache. It helps in saving bandwidth and reducing loading time.

%prep
%setup -n %{name}-%{version}

%build
echo "No building... its python..." > /dev/null

%pre
echo "That's way too old :)" > /dev/null

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT
install -m 755 -d ${RPM_BUILD_ROOT}%{prefix}/etc/
install -m 755 -d ${RPM_BUILD_ROOT}%{prefix}/etc/httpd/conf.d/
install -m 755 -d ${RPM_BUILD_ROOT}%{prefix}/usr/share/videocache/
install -m 744 -d ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/
install -m 744 -d ${RPM_BUILD_ROOT}%{prefix}/usr/sbin/
install -m 744 -d ${RPM_BUILD_ROOT}%{prefix}/var/run/
install -m 744 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/log/videocache/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/youtube/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/facebook/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/metacafe/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/dailymotion/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/vimeo/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/xhamster/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/xvideos/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/redtube/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/xtube/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/wrzuta/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/youporn/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/bing/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/tube8/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/bliptv/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/break/
install -m 755 -o squid -g squid -d  ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache/tmp/
install -m 744 videocache/* -t ${RPM_BUILD_ROOT}%{prefix}/usr/share/videocache/
install -m 644 videocache-sysconfig.conf -T ${RPM_BUILD_ROOT}%{prefix}/etc/videocache.conf
install -m 644 videocache-httpd.conf -T ${RPM_BUILD_ROOT}%{prefix}/etc/httpd/conf.d/videocache.conf
install -m 644 videocache.8.gz -T ${RPM_BUILD_ROOT}%{prefix}/usr/share/man/man8/videocache.8.gz
touch ${RPM_BUILD_ROOT}%{prefix}/var/log/videocache/videocache.log
touch ${RPM_BUILD_ROOT}%{prefix}/var/run/videocache.pid

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

%files
%{prefix}/etc/videocache.conf
%{prefix}/etc/httpd/conf.d/videocache.conf
%{prefix}/usr/share/videocache/
%{prefix}/usr/share/man/man8/videocache.8.gz
%{prefix}/var/log/videocache/
%{prefix}/var/spool/videocache/
%{prefix}/var/run/videocache.pid

%post
if [[ -f %{prefix}/usr/share/videocache/vc-update ]]; then
  ln -f -s %{prefix}/usr/share/videocache/vc-update %{prefix}/usr/sbin/vc-update
fi
if [[ -f %{prefix}/usr/share/videocache/vc-cleaner ]]; then
  ln -f -s %{prefix}/usr/share/videocache/vc-cleaner %{prefix}/usr/sbin/vc-cleaner
fi
if [[ -f %{prefix}/usr/share/videocache/vc-scheduler ]]; then
  ln -f -s %{prefix}/usr/share/videocache/vc-scheduler %{prefix}/usr/sbin/vc-scheduler
fi
if [[ -f %{prefix}/var/log/videocache/videocache.log ]]; then
  rm -f %{prefix}/var/log/videocache/videocache.log
fi
if [[ -f %{prefix}/var/run/videocache.pid ]]; then
  rm -f %{prefix}/var/run/videocache.pid
fi
if [[ -d %{prefix}/var/log/videocache/ ]]; then
  chown -R squid:squid %{prefix}/var/log/videocache/
fi
if [[ -d %{prefix}/var/spool/videocache/ ]]; then
  chown squid:squid %{prefix}/var/spool/videocache/
  chown squid:squid %{prefix}/var/spool/videocache/*
  chmod 755 %{prefix}/var/spool/videocache/
  chmod 755 %{prefix}/var/spool/videocache/*
fi
echo "You need to modify /etc/videocache.conf to make videocache work properly."
echo "Also you need to configure squid. Check videocache manpage for more details."
echo "Please visit http://cachevideos.com/ in case of any problems."

%preun
if [[ -d %{prefix}/var/spool/videocache ]];then
  mv %{prefix}/var/spool/videocache ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocacheff3a11
fi

%postun
if [[ -d %{prefix}/var/spool/videocacheff3a11 ]]; then
  mv %{prefix}/var/spool/videocacheff3a11 ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache
fi
if [[ -h %{prefix}/usr/sbin/vc-update ]]; then
  rm -f %{prefix}/usr/sbin/vc-update
fi
if [[ -h %{prefix}/usr/sbin/vc-cleaner ]]; then
  rm -f %{prefix}/usr/sbin/vc-cleaner
fi
if [[ -h %{prefix}/usr/sbin/vc-scheduler ]]; then
  rm -f %{prefix}/usr/sbin/vc-scheduler
fi

