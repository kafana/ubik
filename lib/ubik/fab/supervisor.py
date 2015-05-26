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

import ConfigParser
import os, os.path
import logging

from ubik import builder

from fabric.api import local, prompt, warn

log = logging.getLogger(__name__)

NAME = 'supervisor'
DEFAULT_CONFDIR = '/etc/opt/lvx/supervisor/conf.d'
SUP_PROGRAM_KEYS = (
    'autostart',
    'command',
    'directory',
    'startsecs',
    'stopwaitsecs',
    'socket',
    'process_name',
    'numprocs',
    'priority',
    'autorestart',
    'startretries',
    'exitcodes',
    'stopsignal',
    'environment',
    'user',
    'events',
    'buffer_size',
    'result_handler',
    'stdout_logfile',
    'stdout_logfile_maxbytes',
    'stdout_logfile_backups',
    'stdout_capture_maxbytes',
    'redirect_stderr',
    'stderr_logfile',
    'stderr_logfile_maxbytes',
    'stderr_logfile_backups',
    'stderr_capture_maxbytes'
)

def _get_config(configfile='package.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    return config

def _source_path(config, section, config_vars):
    source = None
    try:
        source = config.get(section, 'source', vars=config_vars)
    except ConfigParser.NoOptionError:
        pass
    return source

def _source_supervisor_conf(fp, source_path):
    log.info("Sourcing {0} supervisor config file.".format(source_path))
    with open(source_path) as sconfin:
        for line in sconfin:
            fp.write(line)

def _write_supervisor_section(fp, config, section, config_vars, fcgi_section = False):
    try:
        service = config.get(section, 'service', vars=config_vars)
    except ConfigParser.NoOptionError:
        # A section with no service definition is legal for changing config
        # for this module, but it means we have nothing to do here.
        pass
    else:
        if fcgi_section:
            fp.write('[fcgi-program:%s]\n' % service)
        else:
            fp.write('[program:%s]\n' % service)
        for option in SUP_PROGRAM_KEYS:
            if config.has_option(section, option):
                fp.write('%s = %s\n' % (option,
                         config.get(section, option, vars=config_vars)))
        fp.write('\n')

def write_supervisor_config(version, config, env):
    'Creates a configfile to be run by pflex-appsupport supervisord'
    if not isinstance(config, ConfigParser.SafeConfigParser):
        if config:
            config = _get_config(config)
        else:
            config = _get_config()

    # These are the variables that can be percent expanded in the ini
    config_vars = {
        'root': os.path.abspath(env.rootdir),
        'version': version.split('-',1)[0],
    }

    try:
        confdir = config.get(NAME, 'confdir', vars=config_vars)
    except ConfigParser.NoOptionError:
        confdir = DEFAULT_CONFDIR
    local_confdir = os.path.join(env.rootdir, confdir.strip('/'))

    try:
        pkgname = config.get('package', 'name', vars=config_vars)
    except ConfigParser.NoSectionError:
        log.warn("Missing [package] section. Using default name {0}.".format(NAME))
        pkgname = NAME

    confpath = os.path.join(confdir, pkgname + '.conf')
    local_confpath = os.path.join(env.rootdir, confpath.strip('/'))
    if not os.path.exists(local_confdir):
        local('mkdir -m 750 -p %s' % local_confdir, capture=False)

    with open(local_confpath, 'w') as sconf:
        for section in config.sections():
            if section == 'supervisor' or section == 'fcgi-supervisor' or \
                section.startswith('supervisor:') or section.startswith('fcgi-supervisor:'):
                # Check if source param is present, source the conf, and ignore everything else.
                source_path = _source_path(config, section, config_vars)
                if source_path:
                    _source_supervisor_conf(sconf, source_path)
                else:
                    _write_supervisor_section(sconf, config, section, config_vars,
                        fcgi_section=(True if 'fcgi' in section else False))

if __name__ == '__main__':
    basedir = os.path.dirname(os.path.abspath(__file__))
    test_section = """[program:cat]
command=/bin/cat
process_name=%(program_name)s
numprocs=1
directory=/tmp
umask=022
priority=999
autostart=true
autorestart=true
startsecs=10
startretries=3
exitcodes=0,2
stopsignal=TERM
socket=tcp://127.0.0.1:9001
"""
    target = os.path.abspath(os.path.join(basedir, '../../../tests/out/opt/prod'))
    if not os.path.exists(target):
        os.makedirs(target)
    with open(os.path.join(target, "service.conf"), 'w') as f:
        f.write(test_section)
    write_supervisor_config('1.0', '../doc/ini/example-%s.ini' % NAME,
        builder.BuildEnv(rootdir='../tests/out'))
