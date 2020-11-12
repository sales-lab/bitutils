# Copyright 2012 Gabriele Sales <gbrsales@gmail.com>
#
# This file is part of BioinfoTree. It is licensed under the
# terms of the GNU Affero General Public License version 3.

''' Writer for the FASTQ format. '''

from types import StringTypes


class FormatError(Exception):
    ''' Raised to signal an error in a FASTQ block. '''


class FastqWriter(object):
    ''' An streaming FASTQ writer. '''

    def __init__(self, src):
        ''' Opens a FASTQ writer.

            @param src: the path of the file to writer or a file descriptor.
        '''
        if type(src) in StringTypes:
            self.filename = src
            self.fd = file(src, 'w')
            self.own_fd = True
        else:
            self.filename = getattr(src, 'name', '<unknown>')
            self.fd = src
            self.own_fd = False

    def close(self):
        ''' Closes the writer. '''
        if self.own_fd:
            self.fd.close()

    def write(self, label, seq, qual):
        ''' Writes a single FASTQ block.

            @param label: the block label.
            @param seq: the sequence.
            @param qual: the quality string.
        '''
        if len(label) == 0:
            raise FormatError('empty label')
        elif len(seq) != len(qual):
            raise FormatError('sequence and quality values differ in length')

        self.fd.write('@%s\n%s\n+\n%s\n' % (label, seq, qual))
