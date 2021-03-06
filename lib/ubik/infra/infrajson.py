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
#
"""InfraDB JSON-backed Driver"""

import json
import logging

log = logging.getLogger('ubik.infra.infrajson')

class InfraDBDriverJSON(object):
    """InfraDB JSON Driver class

    This provides access to an InfraDB created entirely from a JSON file.  This
    mostly only useful for debugging and unit tests.

    """
    def __init__(self, confstr='infradb.json'):
        """Initialize a new JSON InfraDB Driver

        >>> idb=InfraDBDriverJSON()
        >>> idb.confstr
        'infradb.json'
        >>> len(idb.db['services'])
        0
        >>> idb=InfraDBDriverJSON('tests/infradb.json')
        >>> idb.confstr
        'tests/infradb.json'
        >>> len(idb.db['services'])
        7
        >>>

        """
        log.debug("Initialize InfraDB JSON driver from %s" % confstr)
        self.confstr = confstr
        try:
            with open(confstr, 'r') as idb_fp:
                self.db = json.load(idb_fp)
        except IOError:
            self.db = {'hosts': {}, 'roles': {}, 'services': {}}

    def list_services(self, query=None):
        """Return a list of strings representing all services

        'query' is the optional subdomain

        >>> idb=InfraDBDriverJSON('tests/infradb.json')
        >>> sorted(idb.list_services())
        [u'mailserver', u'webserver']
        >>> sorted(idb.list_services(''))
        [u'mailserver', u'webserver']
        >>> sorted(idb.list_services('dc1'))
        [u'mailserver.dc1', u'webserver.dc1']
        >>>

        """
        if 'services' in self.db:
            if query:
                f = lambda x: query in x
            else:
                f = lambda x: '.' not in x
            return filter(f, self.db['services'].keys())
        return None

    def lookup_host(self, query):
        """Look up a host in the json infra db.  Return dict.

        >>> idb=InfraDBDriverJSON('tests/infradb.json')
        >>> h=idb.lookup_host('alpha.dc1')
        >>> h['name']
        u'alpha.dc1'
        >>> (h['hardware'], h['os'])
        (u'hardware_tag', u'os_tag')
        >>> sorted(h['services'])
        [u'mailserver', u'webserver']
        >>> idb.lookup_host('bogus')
        >>>

        """
        log.debug("Looking up host '%s'" % query)
        host_dict = self.db['hosts'].get(query, None)
        if host_dict and not 'name' in host_dict:
            host_dict[u'name'] = unicode(query)
        return host_dict

    def lookup_service(self, query):
        """Look up a service and return its attributes as a dict

        >>> idb=InfraDBDriverJSON('tests/infradb.json')
        >>> svc=idb.lookup_service('webserver')
        >>> svc['name']
        u'webserver'
        >>> sorted(svc['services'])
        [u'webserver.dc1', u'webserver.dc2']
        >>> svc['hosts']
        [u'delta.dc3']
        >>> len(idb.lookup_service('webserver.dc1')['hosts'])
        2
        >>> idb.lookup_service('bogus')
        >>>

        """
        log.debug("Looking up service '%s'" % query)
        service_dict = self.db['services'].get(query, None)
        if service_dict and not 'name' in service_dict:
            service_dict[u'name'] = unicode(query)
        return service_dict

    def resolve_service(self, query):
        """Resolve a service to a list of hosts

        >>> idb=InfraDBDriverJSON('tests/infradb.json')
        >>> sorted(idb.resolve_service('webserver'))
        [u'alpha.dc1', u'bravo.dc1', u'charlie.dc2', u'delta.dc3']
        >>> sorted(idb.resolve_service('mailserver'))
        [u'alpha.dc1', u'charlie.dc2']
        >>> idb.resolve_service('bogus')
        []
        >>> idb.resolve_service('broken')
        []
        >>>

        """
        log.debug("Looking up service '%s'" % query)
        hosts = []
        service = self.db['services'].get(query, [])
        if 'hosts' in service:
            hosts.extend(service['hosts'])
        if 'services' in service:
            for subservice in service['services']:
                hosts.extend(self.resolve_service(subservice))
        return hosts

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=False)
