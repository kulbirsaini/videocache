#!/bin/bash
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

MESSAGE_LENGTH=70
DOTS='.........................................................................................................'
HYPHENS='---------------------------------------------------------------------------------------------------------'

# Common Functions
blue_without_newline() {
  echo -en "\033[1;36m${1}\033[0m"
}

red_without_newline() {
  echo -en "\033[1;31m${1}\033[0m"
}

green_without_newline() {
  echo -en "\033[1;32m${1}\033[0m"
}

blue() {
  blue_without_newline "$1"; echo
}

dark_blue() {
  echo -e "\033[1;34m${1}\033[0m"
}

red() {
  red_without_newline "$1"; echo
}

green() {
  green_without_newline "$1"; echo
}

strlen() {
  echo `expr "${1}" : '.*'`
}

heading() {
  str_len=`strlen "${1}"`
  dots_before=`expr $((${MESSAGE_LENGTH} - ${str_len})) / 2`
  dots_after=`expr $MESSAGE_LENGTH - $dots_before - $str_len`
  blue "${HYPHENS:0:${dots_before}}${1}${HYPHENS:0:${dots_after}}"
}

message_with_padding() {
  str_len=`strlen "${1}"`
  dots=`expr ${MESSAGE_LENGTH} - ${str_len}`
  blue_without_newline "${1}${DOTS:0:${dots}}"
}

ask_question() {
  for((i = 1; i <= $tries; ++i)); do
    echo -n "$1"
    read choice
    case $choice in
      [yY] | [yY][eE][sS])
      return 1
      break;;
      [nN] | [nN][oO])
      return 0
      break;;
      *)
      if [[ $i == $tries ]]; then
        red "You did not enter a valid input in $tries tries."
        return 2
      else
        red 'Invalid input. Please try again.'
      fi
      ;;
    esac
    echo
  done
}

# Check root access
check_root() {
  message_with_padding 'Checking root access'
  if [[ $UID != 0 ]]; then
    red 'Missing'
    echo
    red 'You must run install.sh as root user or with sudo! Aborting now. Please try again.'
    exit 1
  else
    green 'Granted'
  fi
}

# Yum or Apt-get
detect_installer() {
  which yum > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    installer='yum'
    return 0
  fi
  which apt-get > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    installer='apt-get'
    return 0
  fi
  return 1
}

# Operating system detection and selection
detect_os_from_issue_file() {
  for file in /etc/issue /etc/issue.net; do
    if [[ -f $file ]]; then
      for os_name in Fedora CentOS RedHat Ubuntu Debian; do
        grep -i $os_name $file > /dev/null 2> /dev/null
        if [[ $? == 0 ]]; then
          OS=$os_name
          return 0
        fi
      done
    fi
  done
  return 1
}

detect_os_from_release_file() {
  OS=''
  if [[ -f /etc/fedora-release ]]; then
    OS='Fedora'
  elif [[ -f /etc/redhat-release ]]; then
    for os_name in Fedora CentOS RedHat; do
      grep -i $os_name /etc/redhat-release > /dev/null 2> /dev/null
      if [[ $? == 0 ]]; then
        OS=$os_name
        break
      fi
    done
  elif [[ -f /etc/lsb-release ]]; then
    grep -i Ubuntu /etc/lsb-release > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      OS='Ubuntu'
    fi
  elif [[ -f /etc/debian_version ]] || [[ -f /etc/debian_release ]]; then
    OS='Debian'
  elif [[ -f /etc/slackware-release ]] || [[ -f /etc/slackware-version ]]; then
    OS='Slackware'
  elif [[ -f /etc/mandrake-release ]]; then
    OS='Mandrake'
  elif [[ -f /etc/SUSE-release ]]; then
    OS='Suse'
  elif [[ -f /etc/gentoo-release ]]; then
    OS='Gentoo'
  fi
  if [[ $OS == '' ]]; then
    return 1
  fi
}

detect_os_using_python() {
python - <<END
try:
  import sys
  import platform
  os_dict = { 'fedora' : 'Fedora', 'redhat' : 'RedHat', 'centos' : 'CentOS', 'ubuntu' : Ubuntu, 'debian' : 'Debian', 'gentoo' : 'Gentoo', 'suse' : 'Suse', 'slackware' : 'Slackware', 'mandrake' : 'Mandrake', 'bsd' : 'BSD' }
  os_name = platform.dist('Unknown', 'Unknown', 'Unknown')[0].lower()
  if os_name in os_dict:
    print os_dict[os_name]
    sys.exit(0)
except:
  pass
sys.exit(1)
END
}

detect_os() {
  OS=$(detect_os_using_python)
  if [[ $? == 0 ]]; then
    return 0
  else
    OS=''
  fi
  detect_os_from_issue_file && return 0
  detect_os_from_release_file && return 0
  return 1
}

select_os() {
  declare -a os=('' 'Fedora' 'RedHat' 'CentOS' 'Ubuntu' 'Debian' 'Gentoo' 'Suse' 'Slackware' 'Mandrake' 'BSD' 'Other')
  menu="
  Select your Operating System.\n
  1) ${os[1]} \n
  2) ${os[2]} \n
  3) ${os[3]} \n
  4) ${os[4]} \n
  5) ${os[5]} \n
  6) ${os[6]} \n
  7) ${os[7]} \n
  8) ${os[8]} \n
  9) ${os[9]} \n
  10) ${os[10]}\n
  11) ${os[11]}"
  echo -e $menu
  for((i = 1; i <= $tries; i++)); do
    echo -n "Operating System Choice: "
    read choice
    case $choice in
      1|2|3|4|5|6|7|8|9|10|11)
      OS=${os[$choice]}
      return 0;;
      *)
      if [[ $i == $tries ]]; then
        red "You did not enter a valid input in $tries tries."
      else
        red 'Invalid input. Try again.'
      fi
      ;;
    esac
  done
  return 1
}

detect_or_select_os() {
  want_to_select_os=0
  detect_os
  if [[ $? == 0 ]]; then
    message_with_padding "Automatically detected Operating System"
    green $OS
    echo
    ask_question "Do you want to select your Operating System manually? (y/n): "
    if [[ $? == 1 ]]; then
      want_to_select_os=1
    else
      want_to_select_os=0
    fi
  else
    want_to_select_os=1
  fi
  if [[ $OS == '' ]]; then
    red 'Could not identify your Operating System automatically.'
  fi
  if [[ $OS == '' || $want_to_select_os == 1 ]]; then
    OS=''
    select_os
  fi
}

os_detection() {
  echo; echo
  heading 'Operating System Selection'
  detect_or_select_os
  OS=''
  echo
  if [[ $? == 0 && $OS != '' ]]; then
    message_with_padding "Selected Operating System"
    green $OS
  else
    red "Operating System not detected or specified. Will continue with defaults."
  fi
  echo
}

# Check dependencies
check_pip_or_easy_install() {
  message_with_padding "Checking python-pip"
  which pip > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    green 'Installed'
    return 0
  fi
  which easy_install > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    output=`easy_install install pip 2>&1`
    if [[ $? == 0 ]]; then
      green 'Installed'
      return 0
    else
      red 'Missing'
    fi
  else
    red 'Missing'
  fi
  missing_commands="$missing_commands python-pip"
}

check_command() {
  message_with_padding "Checking ${1}"
  which $1 > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    green 'Installed'
  else
    red 'Missing'
    missing_commands="$missing_commands $1"
  fi
  return 1
}

check_dependencies_basic() {
  echo; echo
  heading 'Early Stage Dependency Check'
  check_command which
}

check_dependencies() {
  echo; echo
  heading 'Full Dependency Check'
  check_command wget
  check_command tar
  check_command gcc
  check_command python
  check_pip_or_easy_install
}

set_missing_packages_for_yum() {
  for command in `echo $missing_commands`; do
    case $command in
      python-pip)
        packages="$packages python-pip"
        break;;
      python)
        packages="$packages python python-devel"
        break;;
      wget)
        packages="$packages wget"
        break;;
      tar)
        packages="$packages tar"
        break;;
      gcc)
        packages="$packages gcc"
        break;;
      apache)
        packages="$packages httpd"
        break;;
      squid)
        packages="$packages squid"
        break;;
      redis)
        packages="$packages redis-server"
        break;;
    esac
  done
}

set_missing_packages_for_apt_get() {
  for command in `echo $missing_commands`; do
    case $command in
      python-pip)
        packages="$packages python-pip"
        break;;
      python)
        packages="$packages python python-dev"
        break;;
      wget)
        packages="$packages wget"
        break;;
      tar)
        packages="$packages tar"
        break;;
      gcc)
        packages="$packages gcc"
        break;;
      apache)
        packages="$packages apache2"
        break;;
      squid)
        packages="$packages squid3"
        break;;
      redis)
        packages="$packages redis-server"
        break;;
    esac
  done
}

set_missing_packages() {
  check_dependencies
  check_squid
  check_apache
  check_redis
  case $installer in
    yum)
      set_missing_packages_for_yum
      ;;
    apt-get)
      set_missing_packages_for_apt_get
      ;;
    *)
      packages=$missing_commands
      ;;
  esac
}

install_missing_packages() {
  check_dependencies_basic
  detect_installer
  set_missing_packages
  if [[ $packages == '' ]]; then
    return 0
  else
    heading "Missing Package Installation"
    red "The following required packages were not found on your system: $packages"
    if [[ $installer == '' ]]; then
      echo
      blue "Please install the required packages before continuing further."
      green "For any help visit support forums at http://cachevideos.com/questions/ or conatct us at http://cachevideos.com/contact"
      exit 1
    else
      ask_question "Do you want me to install the required packages using $installer (y/n): "
      if [[ $? == 1 ]]; then
        $installer install $packages
        echo
        if [[ $? == 0 ]]; then
          green "Successfully installed the required software packags. We are good to proceed."
          echo
        else
          red "Error occured while install required packages. Installer will halt now. Please install required packages and run the installer again."
          green "For any help visit support forums at http://cachevideos.com/questions/ or conatct us at http://cachevideos.com/contact"
          exit 1
        fi
      else
        echo
        blue "Please install the required packages before continuing further."
        green "For any help visit support forums at http://cachevideos.com/questions/ or conatct us at http://cachevideos.com/contact"
        exit 1
      fi
    fi
  fi
}

# Install and verify python modules
remove_file() {
  if [[ $1 != '' && $1 != '/' ]]; then
    if [[ -f $1 ]]; then
      rm -f $1
    fi
  fi
}

remove_dir() {
  if [[ $1 != '' && $1 != '/' ]]; then
    if [[ -d $1 ]]; then
      rm -rf $1
    fi
  fi
}

print_error_and_output() {
  if [[ $1 != '' ]]; then
    red "${1}"
  fi
  if [[ $2 != '' ]]; then
    red "${2}"
  fi
}

download() {
  # Options
  # $1 -> name
  # $2 -> url
  # $3 -> target file name
  # $4 -> error message
  message_with_padding "Fetching ${1}"
  output=`wget --no-check-certificate -q "${2}" -O "${3}" 2>&1`
  if [[ $? == 0 ]]; then
    green 'Done'
  else
    red 'Failed'
    remove_file "$3"
    echo
    print_error_and_output "${4}\nWas trying to fetch $url" "${output}"
    exit 1
  fi
}

extract_archive() {
  # options
  # $1 -> target directory path
  # $2 -> archive path
  # $3 -> error message

  mkdir -p "${1}"
  message_with_padding "Extracting archive ${2}"
  output=`tar -C "${1}" -xzf "${2}" 2>&1`
  if [[ $? == 0 ]]; then
    green 'Done'
  else
    red 'Failed'
    remove_dir "$1"
    remove_file "$2"
    echo
    print_error_and_output "$3" "$output"
    exit 1
  fi
}

verify_python_module() {
  # Options
  # $1 -> name
  message_with_padding "Verifying ${1}"
  output=`python -c "import ${1}" 2>&1`
  if [[ $? == 0 ]]; then
    green 'Verified'
  else
    red 'Failed'
    echo
    print_error_and_output "${output}"
    exit 1
  fi
}

install_python_module() {
  # Options
  # $1 -> Module Name
  message_with_padding "Installing ${1}"
  output=`pip install $1 2>&1`
  if [[ $? == 0 ]]; then
    green 'Success'
  else
    red 'Failed'
    echo
    print_error_and_output "$output"
    red 'Please fix the issues and install this module before continuing further.'
    exit 1
  fi
}

install_and_verify_python_module() {
  # Options
  # $1 -> Import Name
  # $2 -> Module Name

  message_with_padding "Checking ${1}"
  output=`python -c "import ${1}" 2>&1`
  if [[ $? == 0 ]]; then
    green 'Installed'
    return 0
  else
    red 'Missing'
    install_python_module "$2"
    verify_python_module $1
  fi
}

python_import_test() {
python - <<END
import sys
missing_modules = []
for module in ['atexit', 'cgi', 'cookielib', 'cloghandler', 'datetime', 'errno', 'functools', 'glob', 'hiredis', 'iniparse', 'iniparse.config', 'logging', 'logging.handlers', 'netifaces', 'optparse', 'os', 'platform', 'pwd', 'random', 're', 'redis', 'shutil', 'signal', 'socket', 'stat', 'subprocess', 'sys', 'syslog', 'threading', 'time', 'traceback', 'urllib', 'urllib2', 'urlparse' ]:
    try:
        __import__(module)
    except Exception, e:
        missing_modules.append(module)

if len(missing_modules) == 0:
  sys.exit(0)
else:
  print ', '.join(missing_modules)
  sys.exit(1)
END
}

python_code() {
  echo; echo
  heading 'Python Modules And Development Files'
  install_and_verify_python_module setuptools setuptools
  install_and_verify_python_module iniparse iniparse
  install_and_verify_python_module netifaces netifaces
  install_and_verify_python_module cloghandler ConcurrentLogHandler
  install_and_verify_python_module redis redis
  install_and_verify_python_module hiredis hiredis

  message_with_padding "Checking other modules required"
  output=`python_import_test`
  if [[ $? == 0 ]]; then
    green 'Installed'
    return 0
  else
    red 'Missing'
    echo
    red "The following required Python module(s) [${output}] is/are missing."
    red "Please install these modules and run the installer again."
    echo
    exit 1
  fi
}

# Squid user
check_squid_user() {
  if [[ $1 == '' ]]; then
    return 1
  fi
  id $1 > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    return 0
  fi
  return 1
}

guess_squid_user() {
  for user in squid proxy; do
    check_squid_user $user
    if [[ $? == 0 ]]; then
      squid_user=$user; return 0
    fi
  done
}

get_squid_user() {
  echo; echo
  guess_squid_user
  default_squid_user=$squid_user
  if [[ $default_squid_user == '' ]]; then
    echo -n "User who run Squid Proxy Server daemon (example: squid or proxy or nobody): "
  else
    echo -n "User who run Squid Proxy Server daemon (default: ${default_squid_user}): "
  fi

  read choice
  choice=`echo $choice`

  if [[ $choice != '' ]]; then
    squid_user=$choice
  else
    squid_user=$default_squid_user
  fi
  check_squid_user $squid_user
  if [[ $? != 0 ]]; then
    red "WARNING: User \`$squid_user\` doesn't exist on your system. I'll continue anyway."
  fi
  message_with_padding 'Selected user who runs Squid daemon'
  green $squid_user
}

# Squid access.log
is_valid_path() {
  if [[ $2 == 'file' ]]; then
    file=True
  else
    file=False
  fi
python - <<END
import re, sys
if ${file} and "${1}".endswith('/'):
  sys.exit(1)
if re.compile("^/([^\/]+\/){1,7}[^\/]+\/?$").match("${1}"):
  sys.exit(0)
sys.exit(1)
END
}

# Squid
check_squid_with_conf_dir() {
  which $1 > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    for config_file in /etc/squid/squid.conf /etc/squid3/squid.conf /usr/local/etc/squid/squid.conf /usr/local/squid/etc/squid.conf /usr/local/etc/squid3/squid.conf /usr/local/squid3/etc/squid.conf; do
      if [[ -f $config_file ]]; then
        return 0
      fi
    done
  fi
  return 1
}

check_squid() {
  present=0
  message_with_padding "Checking squid"
  for command in squid squid3 /usr/local/sbin/squid /usr/local/sbin/squid3 /usr/local/squid/sbin/squid /usr/local/squid3/sbin/squid; do
    check_squid_with_conf_dir $command
    if [[ $? == 0 ]]; then
      present=1
      break
    fi
  done
  if [[ $present == 0 ]]; then
    red 'Missing'
    echo
    ask_question 'Squid not detected on your system. Do you have Squid installed? (y/n): '
    if [[ $? == 1 ]]; then
      green "Okay, I trust you! Let's move forward."
      echo
    else
      missing_commands="$missing_commands squid"
    fi
  else
    green 'Installed'
  fi
}

# Apache
check_apache_with_conf_dir() {
  which $1 > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    for config_dir in /etc/apache2/conf.d/ /etc/apache/conf.d/ /etc/apache2/conf-enabled/ /etc/apache/conf-enabled/ /etc/httpd/conf.d/ /etc/httpd/extra/ /etc/httpd/conf-enabled/ /etc/apache22/conf.d/ /etc/apache24/conf-enabled/ ; do
      if [[ -d $config_dir ]]; then
        apache_config_dir=$config_dir
        return 0
      fi
    done
  fi
  return 1
}

check_apache() {
  present=0
  message_with_padding "Checking Apache"
  for command in apachectl apache2ctl httpd apache2 apache; do
    check_apache_with_conf_dir $command
    if [[ $? == 0 ]]; then
      present=1
      break
    fi
  done
  if [[ $present == 1 ]]; then
    green 'Installed'
  else
    red 'Missing'
    echo
    ask_question "Apache not detected on your system. Do you have Apache installed? (y/n): "
    if [[ $? == 1 ]]; then
      green "Sure thing! Let's move forward."
    else
      missing_commands="$missing_commands apache"
    fi
  fi
}

get_apache_conf_dir() {
  default_apache_config_dir=$apache_config_dir
  for((i = 1; i <= $tries; i++)); do
    echo
    if [[ $default_apache_config_dir == '' ]]; then
      echo -n "Full path to Apache conf.d or extra directory (example: /etc/httpd/conf.d/): "
    else
      echo -n "Full path to Apache conf.d or extra directory (default: ${default_apache_config_dir}): "
    fi

    read choice
    choice=`echo $choice`

    if [[ $choice == '' && $default_apache_config_dir == '' ]]; then
      if [[ $i == $tries ]]; then
        red "You didn't enter a valid path in $tries tries. Will exit now."
        exit 1
      else
        red "You didn't enter anything. Please try again."
      fi
      continue
    fi

    if [[ $choice != '' ]]; then
      apache_config_dir=$choice
    else
      apache_config_dir=$default_apache_config_dir
    fi

    is_valid_path $apache_config_dir
    if [[ $? == 0 ]]; then
      break
    else
      if [[ $i == $tries ]]; then
        red "You didn't enter a valid path in $tries tries. Will exit now."
        exit 1
      else
        red "Path \`$apache_config_dir\` is either invalid or not acceptable. Please try again."
      fi
    fi
  done
  message_with_padding 'Selected Apache conf.d or extra directory'
  green $apache_config_dir
}

apache_code() {
  echo; echo
  ask_question 'Do you want to skip Apache configuration? (y/n): '
  if [[ $? == 1 ]]; then
    message_with_padding "Apache configuration"
    green "Skipped"
    skip_apache=1
    apache_config_dir=''
  else
    get_apache_conf_dir
  fi
}

# Redis
check_redis() {
  present=0
  message_with_padding "Checking Redis"
  which redis-server > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    green 'Installed'
    present=1
  else
    red 'Missing'
    echo
    ask_question "Redis not detected on your system. Do you have Redis installed? (y/n): "
    if [[ $? == 1 ]]; then
      green "Sure thing! Let's move forward."
    else
      missing_commands="$missing_commands redis"
    fi
    echo
  fi
}

# Client Email
is_valid_email() {
python - <<END
import re, sys
if re.compile("^[^@\ ]+@([A-Za-z0-9]+.){1,3}[A-Za-z]{2,6}$").match("$1"):
  sys.exit(0)
sys.exit(1)
END
}

get_client_email() {
  echo; echo
  heading "Client Email"
  for((i = 1; i <= $tries; ++i)); do
    echo -n "Enter the email address using which you purchased Videocache: "
    read choice
    choice=`echo $choice`
    is_valid_email $choice
    if [[ $? == 1 ]]; then
      if [[ $i == $tries ]]; then
        red "A valid email address was not entered in $tries tries. Will exit now."
        exit 1
      else
        red "Not a valid email address. Please try again."
      fi
    else
      client_email=$choice
      message_with_padding 'Selected email address'
      green $client_email
      return 0
    fi
    echo
  done
}

# Cache Host
is_valid_ip() {
python - <<END
import sys
try:
  if len(filter(lambda x: 0 <= int(x) <= 255, "$1".split('.'))) == 4:
    sys.exit(0)
except Exception, e:
  pass
sys.exit(1)
END
}

is_valid_host_port() {
  return 0
  if [[ `echo $1 | grep "^[0-9\.]\+:[\ ]*$"` != '' ]]; then
    return 1
  fi

  ip_address=`echo $1 | cut -d\: -f1`
  port=`echo $1 | grep ':' | cut -d\: -f2`
  port=`echo $port`
  is_valid_ip $ip_address
  if [[ $? != 0 ]]; then
    return 1
  fi

  if [[ $2 == 'check_port' && $port == '' ]]; then
    return 1
  fi
  if [[ $port != '' ]] && [[ $port -lt 1 || $port -gt 65535 ]]; then
    return 1
  fi
  return 0
}

get_cache_host() {
  echo; echo
  heading "Cache Host (Web Server)"
  ips=`ifconfig | grep inet | grep -v inet6 | grep -v 127.0.0.1 | awk '{print $2}' | cut -d\: -f2 | cut -d\  -f1 | tr '\n' ' '`
  dark_blue "IP address with optional port. It will be used as a web server to serve"
  dark_blue "cached videos. Examples: 192.168.1.14 or 192.168.1.14:8080"
  echo
  for((i = 1; i <= $tries; ++i)); do
    echo -n "Enter IP_Address[:port] for cache_host option (available: ${ips}): "
    read choice
    choice=`echo $choice`
    if [[ $choice != '' ]]; then
      cache_host=$choice
      message_with_padding "Selected cache_host"
      green $cache_host
      return 0
    else
      if [[ $i == $tries ]]; then
        red "You didn't enter a valid IP_Address[:port] in $tries tries. Will exit now."
        exit 1
      else
        red "Entered IP_Address[:port] is not in valid format. Please try again."
      fi
    fi
    echo
  done
}

# This Proxy
get_this_proxy() {
  default_this_proxy=$this_proxy
  echo; echo
  heading 'Squid Proxy Server'
  dark_blue "IP_Address:Port combination for Squid proxy running on this machine."
  dark_blue "Examples: 127.0.0.1:3128 or 192.168.1.1:8080"
  echo
  echo -n "Enter IP_Address:Port for Squid on this machine (default: $default_this_proxy): "
  read choice
  choice=`echo $choice`

  if [[ $choice == '' ]]; then
    this_proxy=$default_this_proxy
  else
    this_proxy=$choice
  fi

  message_with_padding "Selected proxy server"
  green $this_proxy
  return 0
}

# Print Information
print_info() {
  echo; echo
  heading 'Collected Information'

  dark_blue "We will be using the following information to install videocache."
  message_with_padding "Squid user"
  green $squid_user
  message_with_padding "Apache conf.d"
  green $apache_config_dir
  message_with_padding "Email address"
  green $client_email
  message_with_padding "Cache Host"
  green $cache_host
  message_with_padding "Squid proxy"
  green $this_proxy
}

# Install Videocache
build_setup_command() {
  setup_command="python setup.py --squid-user $squid_user --client-email $client_email --cache-host $cache_host --this-proxy $this_proxy"
  if [[ $skip_apache == 0 ]]; then
    setup_command="$setup_command --apache-conf-dir $apache_config_dir"
  else
    setup_command="$setup_command --skip-apache-conf"
  fi
  setup_command="$setup_command install 2>&1"
}

install_videocache() {
  echo; echo
  heading 'Install Videocache'
  build_setup_command
  message_with_padding "Installing Videocache"
  output=`eval $setup_command`
  if [[ $? == 0 ]]; then
    green 'Installed'
    echo
    blue "Command used: $setup_command"
  else
    red 'Failed'
    red "${output}"
    echo
    blue "Command used: $setup_command"
    exit 1
  fi
}

# Install init.d script
install_init_script() {
  echo; echo
  heading 'Install init.d Script'
  message_with_padding "Trying to set default run levels for vc-scheduler"
  which update-rc.d > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    update-rc.d vc-scheduler defaults > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      green 'Done'
      return 0
    fi
  fi

  which chkconfig > /dev/null 2> /dev/null
  if [[ $? == 0 ]]; then
    chkconfig vc-scheduler on > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      green 'Done'
      return 0
    fi
  fi
  red 'Failed'
  echo
  red 'Please check the init script related section of your operating system manual.'
  red 'The videocache scheduler init script is located at /etc/init.d/vc-scheduler .'
  return 1
}

display_instructions() {
  echo; echo
  heading 'Post Installation Instructions'
  if [[ -f instructions.txt ]]; then
    green "Setup has completed successfully. A file instructions.txt has been created\nin the bundle which you should follow to complete the installation process."
    echo
    red "FOLLOW EACH STEP CAREFULLY."
    which cat > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
      cat instructions.txt
    else
      which less > /dev/null 2> /dev/null
      if [[ $? == 0 ]]; then
        less instructions.txt
      fi
    fi
  fi
  echo
}

main() {
  check_root
  install_missing_packages
  #FIXME uncomment these
  python_code
  get_squid_user
  apache_code
  get_client_email
  get_cache_host
  get_this_proxy
  print_info
  install_videocache
  install_init_script
  display_instructions
}

tries=2
OS=''
installer=''
missing_commands=''
squid_user=''
skip_apache=0
apache_config_dir=''
client_email=''
cache_host=''
this_proxy='127.0.0.1:3128'
setup_command=''

main
