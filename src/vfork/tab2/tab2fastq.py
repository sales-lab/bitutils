# Copyright 2012-2021 Gabriele Sales <gbrsales@gmail.com>
#
# This file is part of BioinfoTree. It is licensed under the
# terms of the GNU Affero General Public License version 3.

from optparse import OptionParser
from sys import stdin, stdout
from vfork.fastq.writer import FastqWriter, FormatError
from vfork.io.util import safe_rstrip
from vfork.util import exit, ignore_broken_pipe, format_usage


def main():
    parser = OptionParser(usage=format_usage('''
        %prog <TAB >FASTQ

        Transforms a tab-delimited file with three columns into a FASTQ file.
        Each input row is converted into a FASTQ block.
    '''))
    options, args = parser.parse_args()
    if len(args) != 0:
        exit('Unexpected argument number.')

    writer = FastqWriter(stdout)

    try:
        for lineno, line in enumerate(stdin, 1):
            tokens = safe_rstrip(line).split('\t')
            if len(tokens) != 3:
                exit('Found %d tokens at line %d; expected 3.' % (len(tokens), lineno))

            try:
                writer.write(*tokens)
            except FormatError as e:
                exit('Error writing FASTQ: while processing line %d, %s.' % (lineno, str(e)))

    finally:
        writer.close()


if __name__ == '__main__':
    ignore_broken_pipe(main)
