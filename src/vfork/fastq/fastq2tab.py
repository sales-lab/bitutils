#!/usr/bin/env python
#
# Copyright 2012 Gabriele Sales <gbrsales@gmail.com>
#
# This file is part of BioinfoTree. It is licensed under the
# terms of the GNU Affero General Public License version 3.

from optparse import OptionParser
from sys import stdin, stdout
from vfork.fastq.reader import FastqStreamingReader, FormatError
from vfork.util import ignore_broken_pipe
from vfork.util import exit, format_usage

def main():
    parser = OptionParser(usage=format_usage('''
        Usage: %prog [OPTIONS] <FASTQ >TAB

        Converts a FASTQ file into a TSV file with three columns:
        1) label
        2) sequence
        3) quality
    '''))
    options, args = parser.parse_args()
    if len(args) != 0:
        exit('Unexpected argument number.')

    try:
        for label, seq, qual in FastqStreamingReader(stdin):
            if len(seq) == 0:
                exit('Empty FASTQ sequence in input: ' + label)
            else:
                stdout.write('%s\t%s\t%s\n' % (label, seq, qual))

    except FormatError as e:
        exit('Malformed input: ' + e.args[0])


if __name__ == '__main__':
    ignore_broken_pipe(main)
