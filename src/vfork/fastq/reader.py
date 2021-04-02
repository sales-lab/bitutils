# Copyright 2012 Gabriele Sales <gbrsales@gmail.com>
#
# This file is part of BioinfoTree. It is licensed under the
# terms of the GNU Affero General Public License version 3.

''' Reader for the FASTQ format. '''

from itertools import chain


class FormatError(Exception):
    ''' Raised to signal an error in the format of a FASTQ file. '''

class _ParseIrregularFastq(Exception):
    pass


class FastqStreamingReader(object):
    ''' An optimized, streaming FASTQ reader.

        Validation
        ==========

        This reader doesn't check the contents of sequences
        and qualities. It only verifies that their lengths match.

        As a result, invalid sequence or quality values may
        remain undetected.

        This choice is a tradeoff to gain processing speed.
    '''

    def __init__(self, src):
        ''' Opens a FASTQ reader.

            @param src: the path of the file to read or a file descriptor.
        '''
        if type(src) is str:
            self.filename = src
            self.fd = file(src, 'r')
        else:
            self.filename = getattr(src, 'name', '<unknown>')
            self.fd = src

    def __iter__(self):
        ''' Iterates over the blocks of the FASTQ file.

            @return: an iterator yielding (header, sequence, qualities) tuples.
            @raises FormatError: when the FASTQ file is malformed.
        '''
        fd = self.fd
        lineno = 1

        try:
            while 1:
                inside_block = False
                header  = fd.next(); lineno += 1
                inside_block = True

                seq     = fd.next().rstrip('\r\n'); lineno += 1
                header2 = fd.next(); lineno += 1
                qual    = fd.next().rstrip('\r\n'); lineno += 1

                if header[0] != '@':
                    raise FormatError('invalid FASTQ header in file %s at line %d: %s' % (self.filename, lineno-4, header))
                elif len(header) < 2:
                    raise FormatError('empty FASTQ label in file %s at line %d' % (self.filename, lineno-4))
                elif header2[0] != '+' or len(seq) != len(qual):
                    raise _ParseIrregularFastq

                yield header[1:].rstrip('\r\n'), seq, qual

        except StopIteration:
            if inside_block:
                raise FormatError('incomplete FASTQ block in file %s at line: %d' % (self.filename, lineno))

        except _ParseIrregularFastq:
            lineno -= 4
            fd = chain([header, seq, header2, qual], fd)

            try:
                while 1:
                    inside_block = False
                    header = fd.next(); lineno += 1
                    inside_block = True

                    if header[0] != '@':
                        raise FormatError('invalid FASTQ header in file %s at line %d: %s' % (self.filename, lineno-1, header))
                    elif len(header) < 2:
                        raise FormatError('empty FASTQ label in file %s at line %d' % (self.filename, lineno-1))

                    seq = fd.next().rstrip('\r\n'); lineno += 1
                    while True:
                        another_line = fd.next(); lineno += 1
                        if another_line[0] != '+':
                            seq += another_line.rstrip('\r\n')
                        else:
                            break

                    seq_len = len(seq)
                    qual = ''
                    while 1:
                        qual += fd.next().rstrip('\r\n'); lineno += 1
                        if len(qual) >= seq_len:
                            break

                    if len(qual) > seq_len:
                        raise FormatError('invalid quality in file %s at line %d' % (self.filename, lineno-1))

                    yield header[1:].rstrip('\r\n'), seq, qual

            except StopIteration:
                if inside_block:
                    raise FormatError('incomplete FASTQ block in file %s at line: %d' % (self.filename, lineno))
