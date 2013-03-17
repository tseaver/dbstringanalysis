import collections
import cPickle
import cStringIO
import pprint
import sys
import zlib
import ZODB.FileStorage
import ZODB.serialize

class DummyCache(object):
    def get(self, key, default): return default
    def new_ghost(self, *args): pass

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    # {class {attr -> {value -> count}}}
    results = collections.defaultdict(      # class ->
        lambda : collections.defaultdict(            # addr ->
            lambda : collections.defaultdict(set)))  # type(value) -> value

    class Object(object):

        def __new__(cls, *args):
            return object.__new__(cls)

        def __setstate__(self, state):
            self.state = state
            if isinstance(state, dict):
                for name, value in state.items():
                    if value is None or isinstance(value, basestring):
                        results[self.__class__.__name__][name][
                            str(type(value))].add(value)

    def find_global(conn, module, name):
        name = module + '.' + name
        return Object.__class__(name, (Object, ), {})

    [inp] = args
    it = ZODB.FileStorage.FileIterator(inp)
    reader = ZODB.serialize.ObjectReader(cache=DummyCache(),
                                         factory=find_global)
    for transaction in it:
        for record in transaction:
            if record.data:
                # import pdb; pdb.set_trace()
                data = record.data
                if data.startswith('.z'):
                    data = zlib.decompress(data[2:])
                reader.setGhostState(reader.getGhost(data), data)

    results = {
        cname: {
            aname: dict(av)
            for (aname, av) in cv.items() if len(av) > 1}
        for (cname, cv) in results.items()}

    pprint.pprint({cname: v for cname, v in results.items() if v})

if __name__ == '__main__':
    main()
