''' Reader for the GenePix Axon Text File format. '''

__author__ = "Gabriele Sales <gbrsales@gmail.com>"
__copyright__ = "2011 Gabriele Sales"

from pandas import DataFrame
from types import StringTypes
import re


class ATF(object):
    ''' An object representing an Axon Text File.

        It exposes the following fields:
         - I{headers}: a C{dict} representing optional headers
                       with their values
         - I{table}: a L{DataFrame} with data records
    '''

    def __init__(self, f):
        ''' Reads an ATF file.

            @param f: a file-like object or a filename.
        '''
        if isinstance(f, StringTypes):
            with file(f, 'r') as fd:
                self._load(File(fd))
        else:
            self._load(File(f))

    def _load(self, f):
        self.headers, colnum = self._headers(f)
        labels = self._labels(f, colnum)
        self.table = self._table(f, labels)

    @staticmethod
    def _headers(f):
        l = f.line()
        if l != 'ATF\t1.0':
            raise ValueError('missing ATF header or unsupported version at line 1')

        try:
            nums = [ int(x) for x in f.line().split('\t') ]
            if len(nums) != 2: raise ValueError
        except ValueError:
            raise ValueError('malformed ATF header at line 2')

        hnum, colnum = nums

        hrx = re.compile(r'^"?([^=]+)=([^"]*)"?$')
        headers = {}
        while hnum > 0:
            hnum -= 1

            m = hrx.match(f.line())
            if m is None:
                raise ValueError('malformed optional header at line %d' % f.lineno)

            value = m.group(2)
            headers[m.group(1)] = value if value != '' else None

        return headers, colnum

    @staticmethod
    def _labels(f, colnum):
        labels = [ _strip_quotes(x) for x in f.line().split('\t') ]
        if len(labels) != colnum:
            raise ValueError('unexpected number of column labels at line %d' % f.lineno)

        return labels

    @staticmethod
    def _table(f, labels):
        columns = [ [] for i in xrange(len(labels)) ]

        while True:
            l = f.line(False)
            if l is None: break

            values = l.split('\t')
            if len(values) != len(labels):
                raise ValueError('unexpected number of values at line %d' % f.lineno)

            for i,v in enumerate(values):
                columns[i].append(_strip_quotes(v))

        return DataFrame(dict(zip(labels, columns)))


class File(object):
    def __init__(self, fd):
        self.fd = fd
        self.lineno = 0

    def line(self, ensure_present=True):
        l = self.fd.readline()
        if len(l):
            self.lineno += 1
            return l.rstrip()
        elif ensure_present:
            raise ValueError('unexpected end of file at line %d' % self.lineno)
        else:
            return None


def _strip_quotes(x):
    if x[:1] == '"':
        return x[1:len(x)-1]
    else:
        return x
