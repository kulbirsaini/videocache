%define prefix	/

Name:       videocache
Version:    1.9.6
Release:    1
Summary:    videocache is a squid url rewriter plugin to cache Youtube, Metacafe, Dailymotion, Google, Vimeo, Redtube, Xtube, Youporn, MSN Soapbox, Tube8, TV UOL(BR), Blip TV and Break.com Videos and Wrzuta.pl audio.
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
echo "You need to modify /etc/videocache.conf to make videocache work properly."
echo "Also you need to configure squid. Check videocache manpage for more details."
echo "Please visit http://cachevideos.com/ in case of any problems."

%preun
if [[ -d %{prefix}/var/spool/videocache ]];then
  mv %{prefix}/var/spool/videocache ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache12345
fi

%postun
if [[ -d %{prefix}/var/spool/videocache1 ]]; then
  mv %{prefix}/var/spool/videocache12345 ${RPM_BUILD_ROOT}%{prefix}/var/spool/videocache
fi

