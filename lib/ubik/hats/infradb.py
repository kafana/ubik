
import logging
import os.path

import ubik.infra.db
import ubik.defaults

from ubik.hats import HatException
from ubik.hats.base import BaseHat

log = logging.getLogger('ubik.hats.infradb')

class InfraDBHat(BaseHat):
    "Infra DB Lookup Hat"

    name = 'infradb'
    desc = "Infra DB lookups"

    @staticmethod
    def areyou(string):
        "Confirm or deny whether I am described by string"
        if string == 'hosts':
            return True
        return False

    def __init__(self, args, config=None, options=None):
        super(InfraDBHat, self).__init__(args, config, options)
        self.args = args
        import pdb; pdb.set_trace()

        cache_dir = os.path.expanduser(self.config.get('cache','dir'))
        self.cache = ubik.cache.UbikPackageCache(cache_dir)

    def run(self):
        if len(self.args) == 0:
            self.args.insert(0, 'ls')

        try:
            while len(self.args) > 0:
                command = self.args.pop(0)
                if command in self.command_map:
                    self.command_map[command](self)
                elif command == 'help':
                    self.help(self.output)
                else:
                    raise HatException("Unknown cache command: %s" % command)
        except ubik.cache.CacheException as e:
            raise HatException(str(e))

    # cache sub-commands
    # these functions are expected to consume self.args
    def add(self):
        '''cache add FILE

        Adds FILE to the package cache.'''
        i = 0
        for filepath in self.args:
            i += 1
            if filepath == ';':
                break
            self.cache.add(filepath)
        del self.args[:i]

    def ls(self):
        '''cache [ ls [ GLOB ] ]

        Display the contents of the cache, potentially filtered by GLOB.
        '''
        if len(self.args) == 0:
            self.args.insert(0, '*')
        i = 0
        for glob in self.args:
            i += 1
            for pkg in self.cache.list(glob):
                print pkg["filename"]
        del self.args[:i]

    def prune(self):
        '''cache prune

        Prune contents of cache according to cache.keep_packages setting.
        Also tidies the index by removing packages that have been deleted
        on disk.
        '''
        self.cache.prune()

    def remove(self):
        '''cache remove FILENAME

        Find and remove the file named FILENAME from the package cache.'''
        i = 0
        for filepath in self.args:
            i += 1
            if filepath == ';':
                break
            self.cache.remove(filepath)
        del self.args[:i]

    command_list = ( add, ls, prune, remove )
    command_map = {
        'add':      add,
        'del':      remove,
        'delete':   remove,
        'list':     ls,
        'ls':       ls,
        'prune':    prune,
        'remove':   remove,
        'rm':       remove,
    }

if __name__ == '__main__':
    InfraDBHat(())

