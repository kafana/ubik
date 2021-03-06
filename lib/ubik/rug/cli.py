#!/usr/bin/python
#
# Copyright 2012 Lee Verberne <lee@blarg.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Command line front end to all these hats
"This is the command line interface to a collection of platform control scripts"

import logging
import optparse
import os
import sys

import ubik.config
import ubik.defaults
import ubik.hats

config = ubik.config.UbikConfig()
options = None
log = logging.getLogger('rug.cli')

def init_cli(args=None):
    global config, options
    p = optparse.OptionParser(usage='%prog [global_options] COMMAND [ARG ...]',
                              version='%prog ' + ubik.defaults.VERSION,
                              description=__doc__,
                              epilog='Use the help sub-command for more '
                                     'details.')
    p.add_option('--conf', '-c', metavar='FILE',
                 default=ubik.defaults.CONFIG_FILE,
                 help='Use config FILE instead of %default')
    p.add_option('--debug', '-d', action='store_true',
                 help='Enable debug logging')
    p.add_option('--workdir', metavar='DIR',
                 help="Use DIR as working directory, creating if necessary")
    p.add_option('--verbose', '-v', action='store_true',
                 help='Enable verbose logging')
    p.disable_interspersed_args()
    (options, args) = p.parse_args(args=args)

    if 'DEBUG' in os.environ:
        options.debug = True
    if options.debug:
        log.setLevel(logging.DEBUG)
    elif options.verbose:
        log.setLevel(logging.INFO)

    if 'RUG_GLOBAL_CONFIG' in os.environ:
        global_cf = os.environ['RUG_GLOBAL_CONFIG']
    else:
        global_cf = ubik.defaults.GLOBAL_CONFIG_FILE
    config.read(options.conf, global_cf)

    if len(args) == 0:
        args = ['help',]

    return args

def main(args=None):
    args = init_cli(args)

    # Try to figure out what hat we're using here
    hat = ubik.hats.hatter(args, config, options)
    if hat:
        try:
            hat.run()
        except ubik.hats.HatException as e:
            print >>sys.stderr, "ERROR:", str(e)
            if options.debug:
                raise e
            return 1
    else:
        print >>sys.stderr, "ERROR: No such command"
        return 2

if __name__ == '__main__':
    sys.exit(main())

