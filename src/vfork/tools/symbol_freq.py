# Copyright 2012-2021 Paolo Martini <paolo.cavei@gmail.com>

from optparse import OptionParser
from os.path import basename
from sys import argv, exit, stdin
from vfork.util import exit
from vfork.io.util import safe_rstrip


def collect(symbols):
    counts = {}
    total = 0
    for symbol in symbols:
        counts[symbol] = counts.get(symbol, 0) + 1
        total += 1
    return counts, total


def main():
    parser = OptionParser(usage='%prog <SYMBOLS')
    parser.add_option('-r', '--reverse', dest='reverse', action='store_true', default=False,
                      help='print count before symbol')
    parser.add_option('-d', '--double', dest='double', action='store_true', default=False,
                      help='same as symbol_count | cut -f 2 | symbol_count')
    options, args = parser.parse_args()
    if len(args) != 0:
        exit('Unexpected argument number.')

    mode = 'count' if basename(argv[0]) == 'symbol_count' else 'freq'
    if options.double and mode == 'freq':
        exit("Double option only supported for symbol_count.")

    counts, total = collect(safe_rstrip(line) for line in stdin)
    if options.double:
        counts, total = collect(iter(counts.values()))

    for symbol in sorted(counts.keys()):
        count = counts[symbol]
        if mode == 'count':
            if options.reverse:
                print('%d\t%s' % (count, str(symbol)))
            else:
                print('%s\t%d' % (str(symbol), count))
        else:
            if options.reverse:
                print('%g\t%s' % (count / total, symbol))
            else:
                print('%s\t%g' % (symbol, count / total))


if __name__ == '__main__':
    main()
