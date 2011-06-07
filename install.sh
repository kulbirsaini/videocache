#!/bin/bash
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

SETUPTOOLS_URL='http://pypi.python.org/packages/source/s/setuptools/setuptools-0.6c11.tar.gz'
SETUPTOOLS_FILENAME='setuptools.tar.gz'
SETUPTOOLS_DIR='setuptools'

NETIFACES_URL='http://pypi.python.org/packages/source/n/netifaces/netifaces-0.4.tar.gz'
NETIFACES_FILENAME='netifaces.tar.gz'
NETIFACES_DIR='netifaces'

INIPARSE_URL='http://iniparse.googlecode.com/files/iniparse-0.4.tar.gz'
INIPARSE_FILENAME='python-iniparse.tar.gz'
INIPARSE_DIR='python-iniparse'

blue() {
  echo -en "\033[0;34m${1}\033[0m"
}

red() {
  echo -en "\033[0;31m${1}\033[0m"
}

green() {
  echo -en "\033[0;32m${1}\033[0m"
}

install_setuptools() {
  blue 'Checking python-setuptools...............'
  python -c 'import setuptools' > /dev/null 2> /dev/null
  if [[ $? != 0 ]]; then
    red 'Missing'; echo
    blue 'Fetching python-setuptools...............'
    wget -q $SETUPTOOLS_URL -O /tmp/$SETUPTOOLS_FILENAME
    green 'Done'; echo
    mkdir -p /tmp/$SETUPTOOLS_DIR
    blue 'Extracting python-setuptools.............'
    tar -C /tmp/$SETUPTOOLS_DIR -xzf /tmp/$SETUPTOOLS_FILENAME
    green 'Done'; echo
    blue 'Installing python-setuptools.............'
    cur_dir=`pwd`
    cd /tmp/$SETUPTOOLS_DIR/*
    python setup.py -q install > /dev/null
    if [[ $? == 0 ]]; then
      green 'Success'; echo
    fi
    cd $cur_dir
    rm -rf /tmp/$SETUPTOOLS_DIR
    rm -f /tmp/$SETUPTOOLS_FILENAME
    blue 'Testing python-setuptools................'
    python -c 'import setuptools' > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      green 'Verified'; echo
    else
      red 'Failed'; echo
    fi
    echo
  else
    green 'Installed'; echo
  fi
}

install_iniparse() {
  blue 'Checking python-iniparse.................'
  python -c 'import iniparse' > /dev/null 2> /dev/null
  if [[ $? != 0 ]]; then
    red 'Missing'; echo
    blue 'Fetching python-iniparse.................'
    wget -q $INIPARSE_URL -O /tmp/$INIPARSE_FILENAME
    green 'Done'; echo
    mkdir -p /tmp/$INIPARSE_DIR
    blue 'Extracting python-iniparse...............'
    tar -C /tmp/$INIPARSE_DIR -xzf /tmp/$INIPARSE_FILENAME
    green 'Done'; echo
    blue 'Installing python-iniparse...............'
    cur_dir=`pwd`
    cd /tmp/$INIPARSE_DIR/*
    python setup.py -q install > /dev/null
    if [[ $? == 0 ]]; then
      green 'Success'; echo
    fi
    cd $cur_dir
    rm -rf /tmp/$INIPARSE_DIR
    rm -f /tmp/$INIPARSE_FILENAME
    blue 'Testing python-iniparse..................'
    python -c 'import iniparse' > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      green 'Verified'; echo
    else
      red 'Failed'; echo
    fi
    echo
  else
    green 'Installed'; echo
  fi
}

install_netifaces() {
  blue 'Checking python-netifaces................'
  python -c 'import netifaces' > /dev/null 2> /dev/null
  if [[ $? != 0 ]]; then
    red 'Missing'; echo
    blue 'Fetching python-netifaces................'
    wget -q $NETIFACES_URL -O /tmp/$NETIFACES_FILENAME
    green 'Done'; echo
    mkdir -p /tmp/$NETIFACES_DIR
    blue 'Extracting python-netifaces..............'
    tar -C /tmp/$NETIFACES_DIR -xzf /tmp/$NETIFACES_FILENAME
    green 'Done'; echo
    blue 'Installing python-netifaces..............'
    cur_dir=`pwd`
    cd /tmp/$NETIFACES_DIR/*
    python setup.py -q install > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      green 'Success'; echo
    fi
    cd $cur_dir
    rm -rf /tmp/$NETIFACES_DIR
    rm -f /tmp/$NETIFACES_FILENAME
    blue 'Testing python-netifaces.................'
    python -c 'import netifaces' > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      green 'Verified'; echo
    else
      red 'Failed'; echo
    fi
  else
    green 'Installed'; echo
  fi
}

check_python_dev() {
  blue 'Checking Python.h........................'
  pythonh=`python -c 'import setuptools; print setuptools.distutils.sysconfig.get_python_inc()'`
  if [[ -f ${pythonh}/Python.h ]]; then
    green 'Found'; echo
    return 0
  else
    red 'Missing'; echo
    echo; red 'Please install python-dev or python-devel package depending on your operating system.'; echo
  fi
  exit 1
}

install_videocache() {
  blue 'Installing Videocache....................'
  output=`python setup.py install 2>&1`
  if [[ $? == 0 ]]; then
    green 'Installed'; echo
    green "${output}"; echo
  else
    red 'Failed'; echo
    red "${output}"; echo
  fi
}

check_apache_with_conf_dir() {
  which $1 > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    if [[ -d /etc/apache2/conf.d/ ]]; then
      green 'Installed'; echo
      return 0
    elif [[ -d /etc/apache/conf.d/ ]]; then
      green 'Installed'; echo
      return 0
    elif [[ -d /etc/httpd/conf.d/ ]]; then
      green 'Installed'; echo
      return 0
    fi
  fi
  return 1
}

check_apache() {
  blue 'Checking apache..........................'
  for command in apachectl apache2ctl httpd apache2 apache; do
    check_apache_with_conf_dir $command
    if [[ $? == 0 ]]; then
      return 0
    fi
  done
  red 'Missing'; echo
  echo; red 'Download and install apache from http://www.apache.org/ or check your operating system manual for installing the same.'; echo
  exit 1
}

check_command() {
  blue "${2}"
  which $1 > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    green 'Installed'; echo
  else
    red 'Missing'; echo
    echo; red "${3}"; echo
    exit 1
  fi
}

check_dependencies() {
  check_command python 'Checking python..........................' 'Download and install python from http://www.python.org/ or check your operating system manual for installing the same.'
  check_command wget 'Checking wget............................' 'Download and install wget from http://www.gnu.org/software/wget/ or check your operating system manual for installing the same.'
  check_command tar 'Checking tar.............................' 'Download and install tar from http://www.gnu.org/software/tar/ or check your operating system manual for installing the same.'
  check_command gcc 'Checking gcc.............................' 'Download and install gcc from http://gcc.gnu.org/ or check your operating system manual for installing the same.'
  check_apache
}

check_dependencies
install_setuptools
check_python_dev
install_iniparse
install_netifaces
install_videocache

