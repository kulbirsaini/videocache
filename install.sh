#!/bin/bash
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

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

install_iniparse() {
  blue 'Checking python-iniparse.................'
  python -c 'import iniparse' > /dev/null 2> /dev/null
  if [[ $? != 0 ]]; then
    red 'Missing.'; echo
    blue 'Fetching python-iniparse.................'
    wget -q $INIPARSE_URL -O /tmp/$INIPARSE_FILENAME
    green 'Done.'; echo
    mkdir -p /tmp/$INIPARSE_DIR
    blue 'Extracting python-iniparse...............'
    tar -C /tmp/$INIPARSE_DIR -xzf /tmp/$INIPARSE_FILENAME
    green 'Done.'; echo
    blue 'Installing python-iniparse...............'
    cur_dir=`pwd`
    cd /tmp/$INIPARSE_DIR/*
    python setup.py -q install > /dev/null
    if [[ $? == 0 ]]; then
      green 'Success.'; echo
    fi
    cd $cur_dir
    rm -rf /tmp/$INIPARSE_DIR
    rm -f /tmp/$INIPARSE_FILENAME
    blue 'Testing python-iniparse..................'
    python -c 'import iniparse' > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      green 'Verified.'; echo
    else
      red 'Failed.'; echo
    fi
    echo
  else
    green 'Installed.'; echo
  fi
}

install_netifaces() {
  blue 'Checking python-netifaces................'
  python -c 'import netifaces' > /dev/null 2> /dev/null
  if [[ $? != 0 ]]; then
    red 'Missing.'; echo
    blue 'Fetching python-netifaces................'
    wget -q $NETIFACES_URL -O /tmp/$NETIFACES_FILENAME
    green 'Done.'; echo
    mkdir -p /tmp/$NETIFACES_DIR
    blue 'Extracting python-netifaces..............'
    tar -C /tmp/$NETIFACES_DIR -xzf /tmp/$NETIFACES_FILENAME
    green 'Done.'; echo
    blue 'Installing python-netifaces..............'
    cur_dir=`pwd`
    cd /tmp/$NETIFACES_DIR/*
    python setup.py -q install > /dev/null
    if [[ $? == 0 ]]; then
      green 'Success.'; echo
    fi
    cd $cur_dir
    rm -rf /tmp/$NETIFACES_DIR
    rm -f /tmp/$NETIFACES_FILENAME
    blue 'Testing python-netifaces.................'
    python -c 'import netifaces' > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      green 'Verified.'; echo
    else
      red 'Failed.'; echo
    fi
  else
    green 'Installed.'; echo
  fi
}

install_iniparse
install_netifaces

