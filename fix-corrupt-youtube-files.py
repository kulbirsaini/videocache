#!/usr/bin/env python

from optparse import OptionParser
import re, os, glob

parser = OptionParser()
parser.add_option('-r', '--remove', dest = 'remove', action = "store_true", default = False, help = "Remove corrupt files")
parser.add_option('-s', '--show', dest = 'show', action = "store_true", default = False, help = "Show names of corrupt files")
parser.add_option('-d', '--dir', dest = 'dir', type = 'string', help = "Absolute pat the youtube cache directory", default = '/var/spool/videocache/youtube')
options, args = parser.parse_args()
options.dir = options.dir.rstrip('/')

regex1 = re.compile('^[a-zA-Z0-9_\-]{11}_[0-9]+_[0-9]+_[0-9]+')
regex2 = re.compile('^[a-zA-Z0-9_\-]{16}_[0-9]+_[0-9]+_[0-9]+')

corrupt_files = []
os.chdir(options.dir)
for filename in filter(lambda x: regex1.search(x) or regex2.search(x), os.listdir(options.dir)):
    p = map(lambda x: int(x), filename.split('.')[0].split('_')[-2:])
    expected = p[1] - p[0] + 1
    actual = os.path.getsize(filename)
    if abs(actual - expected) > 1024:
        corrupt_files.append(filename)

if options.show:
    if len(corrupt_files) > 0:
        print '\n'.join(map(lambda x: options.dir + '/' + x, corrupt_files))
        print; print 'Total ', len(corrupt_files), 'corrupt files'
    else:
        print 'Yay! No corrupt files found.'
elif options.remove:
    for filename in corrupt_files:
        os.unlink(filename)
        print 'Removed', options.dir + '/' + filename

    if len(corrupt_files) > 0:
        print; print 'Removed', len(corrupt_files), 'corrupt files'
    else:
        print 'Yay! No corrupt files found.'
else:
    parser.print_help()
