# Copyright 2012 Gabriele Sales <gbrsales@gmail.com>
#
# This file is part of BioinfoTree. It is licensed under the
# terms of the GNU Affero General Public License version 3.

''' A collection of classes for reading and writing FASTQ files. '''

from .reader import FastqStreamingReader, FormatError
from .writer import FastqWriter
