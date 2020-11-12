''' A collection of classes for reading and writing FASTA files. '''

from reader import SingleBlockReader, MultipleBlockReader, MultipleBlockStreamingReader, FormatError
from writer import SingleBlockWriter
