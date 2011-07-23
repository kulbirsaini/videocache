#!/bin/bash
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

MESSAGE_LENGTH=60
MESSAGE_STR='...............................................................................................'

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

strlen() {
  echo `expr length "${1}"`
}

message_with_padding() {
  str_len=`strlen "${1}"`
  dots=`expr ${MESSAGE_LENGTH} - ${str_len}`
  blue "${1}${MESSAGE_STR:0:${dots}}"
}

# Options
# $1 -> Name
# $2 -> URL
# $3 -> Archive Filename
# $4 -> Archive Directory Name
install_python_module() {
  message_with_padding "Checking python-${1}"
  output=`python -c "import ${1}" 2>&1`
  if [[ $? != 0 ]]; then
    red 'Missing'; echo

    message_with_padding "Fetching python-${1}"
    output=`wget -q "${2}" -O /tmp/"${3}" 2>&1`
    if [[ $? == 0 ]]; then
      green 'Done'; echo
    else
      red 'Failed'; echo
      echo; red 'Please check your network connection!'; echo; red "${output}"; echo
      exit 1
    fi

    mkdir -p "/tmp/${4}"
    message_with_padding "Extracting python-${1}"
    output=`tar -C /tmp/"${4}" -xzf /tmp/"${3}" 2>&1`
    if [[ $? == 0 ]]; then
      green 'Done'; echo
    else
      red 'Failed'; echo
      echo; red "${output}"; echo
      exit 1
    fi

    message_with_padding "Installing python-${1}"
    cur_dir=`pwd`
    cd /tmp/"${4}"/*
    output=`python setup.py install 2>&1`
    if [[ $? == 0 ]]; then
      green 'Success'; echo
    else
      red 'Failed'; echo
      echo; red "${output}"; echo
      exit 1
    fi
    cd $cur_dir
    rm -rf /tmp/"${4}"
    rm -f /tmp/"${3}"

    message_with_padding "Testing python-${1}"
    output=`python -c "import ${1}" 2>&1`
    if [[ $? == 0 ]]; then
      green 'Verified'; echo
    else
      red 'Failed'; echo
      echo; red "${output}"; echo
      exit 1
    fi
    echo
  else
    green 'Installed'; echo
  fi
}

check_python_dev() {
  message_with_padding "Checking Python.h"
  pythonh=`python -c 'import setuptools; print setuptools.distutils.sysconfig.get_python_inc()' 2>&1`
  if [[ $? != 0 ]]; then
    red 'Failed'; echo
    echo; red "${pythonh}"; echo
    exit 1
  fi

  if [[ -f ${pythonh}/Python.h ]]; then
    green 'Installed'; echo
    return 0
  else
    red 'Missing'; echo
    echo; red 'Please install python-dev or python-devel package depending on your operating system.'; echo
  fi
  exit 1
}

install_videocache() {
  message_with_padding "Installing Videocache"
  output=`python setup.py install 2>&1`
  if [[ $? == 0 ]]; then
    green 'Installed'; echo
    green "${output}"; echo
  else
    red 'Failed'; echo
    red "${output}"; echo
    exit 1
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
  message_with_padding "Checking apache"
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
  message_with_padding "Checking ${1}"
  which $1 > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    green 'Installed'; echo
  else
    red 'Missing'; echo
    echo; red "${2}"; echo
    exit 1
  fi
}

check_dependencies() {
  check_command which 'Download and install which from http://www.gnu.org/software/which/ or check your operating system manual for installing the same.'
  check_command bash 'Download and install bash from http://www.gnu.org/software/bash/ or check your operating system manual for installing the same.'
  check_command python 'Download and install python from http://www.python.org/ or check your operating system manual for installing the same.'
  check_command wget 'Download and install wget from http://www.gnu.org/software/wget/ or check your operating system manual for installing the same.'
  check_command tar 'Download and install tar from http://www.gnu.org/software/tar/ or check your operating system manual for installing the same.'
  check_command gcc 'Download and install gcc from http://gcc.gnu.org/ or check your operating system manual for installing the same.'
  check_apache
}

check_root() {
  if [[ $UID != 0 ]]; then
    red 'You must be logged in as root to install videocache!'; echo
    exit 1
  fi
}

install_init_script() {
  message_with_padding "Trying to set default run levels for vc-scheduler"
  which update-rc.d > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    update-rc.d vc-scheduler defaults > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      green 'Done'; echo
      return
    fi
  fi

  which chkconfig > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    chkconfig vc-scheduler on > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      green 'Done'; echo
      return 0
    fi
  fi
  red 'Failed'; echo
  red 'Please check the init script related section of your operating system manual.'; echo
  red 'The videocache scheduler init script is located at /etc/init.d/vc-scheduler .'; echo
  return 1
}

check_root
check_dependencies
install_python_module iniparse "${INIPARSE_URL}" "${INIPARSE_FILENAME}" "${INIPARSE_DIR}"
install_python_module setuptools "${SETUPTOOLS_URL}" "${SETUPTOOLS_FILENAME}" "${SETUPTOOLS_DIR}"
check_python_dev
install_python_module netifaces "${NETIFACES_URL}" "${NETIFACES_FILENAME}" "${NETIFACES_DIR}"
install_videocache
install_init_script
echo

