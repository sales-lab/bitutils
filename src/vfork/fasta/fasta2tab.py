#!/usr/bin/env python
#
# Copyright 2010 Gabriele Sales <gbrsales@gmail.com>

from optparse import OptionParser
from sys import stdin

from vfork.fasta.reader import MultipleBlockStreamingReader, FormatError
from vfork.util import exit, format_usage
from vfork.util import ignore_broken_pipe


def main():
    parser = OptionParser(usage=format_usage('''
    Usage: %prog [OPTIONS] <FASTA >TAB

    Converts a FASTA file into a TSV file with two columns:
    1) label
    2) sequence
    '''))

    parser.add_option('-e', '--allow-empty', dest='allow_empty', default=False, action='store_true',
                      help='allow empty sequences')
    parser.add_option('-m', '--multi-line', dest='multi', default=False, action='store_true',
                      help='keep sequences split over multiple lines, each one prefixed by the sequence label')
    options, args = parser.parse_args()
    if len(args) != 0:
        exit('Unexpected argument number.')

    try:
        for label, seq in MultipleBlockStreamingReader(stdin, join_lines=not options.multi):
            if options.multi:
                seq = list(seq)

            empty_seq = len(seq) == 0
            if empty_seq:
                if not options.allow_empty:
                    exit('Empty FASTA sequence in input: ' + label)
                else:
                    print(label + '\t')
            else:
                if options.multi:
                    for s in seq:
                        print('%s\t%s' % (label, s))
                else:
                    print('%s\t%s' % (label, seq))

    except FormatError as e:
        exit('Malformed FASTA input: ' + e.args[0])


if __name__ == '__main__':
    ignore_broken_pipe(main)
