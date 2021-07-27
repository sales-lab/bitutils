#!/usr/bin/env python
#
# Copyright 2011 Paolo Martini <paolo.cavei@gmail.com>

from itertools import groupby
from operator import itemgetter
from optparse import OptionParser
from sys import stdin, stdout
from vfork.fasta.writer import MultipleBlockWriter
from vfork.io.util import safe_rstrip, parse_int
from vfork.util import exit, format_usage, ignore_broken_pipe


def read_line(fd, col, is_sorted):
    pre_id = None
    length_t = None
    for lineidx, line in enumerate(fd):
        tokens = safe_rstrip(line).split('\t')
        if length_t is not None and length_t != len(tokens):
            exit("Malformed input: incorrect number of columns at line %s" % (lineidx + 1))
        length_t = len(tokens)
        if not is_sorted:
            if pre_id is not None and tokens[0] < pre_id:
                exit("Malformed input: lexicographically sorted on col 1 at line %s" % (lineidx + 1))
        pre_id = tokens[0]
        if col >= len(tokens):
            exit("Wrong column specification.")
        seq = tokens[col]
        key = tuple(tokens[:col] + tokens[(col + 1):])
        yield key, seq


def main():
    parser = OptionParser(usage=format_usage('''
        %prog COL <TSV >FASTA

        Transforms a tab-delimited into a FASTA file;
                COL indicate the column containing the sequence,
                others fields set as header.
    '''))

    parser.add_option('-s', '--already-sorted', dest='already_sorted', action='store_true', default=False,
                      help='assume input already sorted on firs column.')
    parser.add_option('-m', '--multi-line', dest='multi', action='store_true', default=False,
                      help='collapse equal headers: header contents are printed one per line.')
    parser.add_option('-c', '--concatenate-seq', dest='concatenate', action='store_true', default=False,
                      help='collapses equal headers and concatenate their contents in strict-fasta format')
    options, args = parser.parse_args()

    if len(args) != 1:
        exit('Unexpected argument number.')

    col = parse_int(args[0], 'COL', 'strict_positive') - 1
    writer = MultipleBlockWriter(stdout)

    if options.multi or options.concatenate:
        for ID, grp in groupby(read_line(stdin, col, options.already_sorted), itemgetter(0)):
            group = list(grp)
            if options.concatenate:
                seq = ''.join([s[1] for s in group])
                writer.write_header('\t'.join(ID))
                writer.write_sequence(seq)
            else:
                print(">%s" % '\t'.join(ID))
                for i in range(len(group)):
                    print(group[i][1])
        writer.flush()
    else:
        for ID, seq in read_line(stdin, col, options.already_sorted):
            writer.write_header('\t'.join(ID))
            writer.write_sequence(seq)
        writer.flush()


if __name__ == '__main__':
    ignore_broken_pipe(main)
