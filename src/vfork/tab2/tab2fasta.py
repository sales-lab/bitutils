# Copyright 2021 Paolo Martini <paolo.cavei@gmail.com>

from optparse import OptionParser
from sys import stdin

from vfork.io.util import safe_rstrip
from vfork.util import exit, format_usage


def main():
    parser = OptionParser(usage=format_usage('''
        %prog <TAB >FASTA
        Transforms a tab-delimited file with two columns into a FASTA file;
        each row in the input is converted into a FASTA block.
    '''))

    parser.add_option('-s', '--already_sorted', dest='already_sorted', action='store_true',
                      default=False, help='assume input already sorted on firs column.')

    options, args = parser.parse_args()

    if len(args) == 0:
        pass
    else:
        exit('Unexpected argument number.')

    pre_id = None
    for lineidx, line in enumerate(stdin):
        line = safe_rstrip(line)
        tokens = line.split('\t')
        fatst_id = tokens[0]
        if pre_id is None or fatst_id != pre_id:
            if pre_id > fatst_id and not options.already_sorted:
                exit("Input not lexicographically sorted on col 1.")
            print(">%s" % tokens[0])
        print("\t".join(tokens[1:]))
        pre_id = fatst_id


if __name__ == '__main__':
    main()
