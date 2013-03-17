import collections
import cPickle
import cStringIO
import pprint
import sys
import zlib
import ZODB.FileStorage

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

    def find_global(module, name):
        name = module + '.' + name
        return Object.__class__(name, (Object, ), {})

    [inp] = args
    it = ZODB.FileStorage.FileIterator(inp)
    for transaction in it:
        for record in transaction:
            if record.data:
                # import pdb; pdb.set_trace()
                data = record.data
                if data.startswith('.z'):
                    data = zlib.decompress(data[2:])
                u = cPickle.Unpickler(cStringIO.StringIO(data))
                u.persistent_load = lambda x: None
                u.find_global = find_global
                class_ = u.load()
                if isinstance(class_, tuple):
                    class_ = class_[0]
                state = u.load()
                class_.__new__(class_).__setstate__(state)

    results = {
        cname: {
            aname: dict(av)
            for (aname, av) in cv.items() if len(av) > 1}
        for (cname, cv) in results.items()}

    pprint.pprint({cname: v for cname, v in results.items() if v})

if __name__ == '__main__':
    main()
