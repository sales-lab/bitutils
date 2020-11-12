from __future__ import with_statement

from cStringIO import StringIO
from mmap import mmap, ACCESS_READ
from os import fstat, linesep, SEEK_SET
from types import IntType, StringTypes
from ..sequence import make_sequence_filter
from ..io.colreader import Reader
from ..io.util import safe_rstrip

class RandomAccessSequence(object):
	''' A mixin for random access sequences. '''
	
	def __len__(self):
		return self.size
	
	def __getitem__(self, key):
		raise NotImplementedError
	
	def _key_to_range(self, key):
		if isinstance(key, slice):
			if key.start is None:
				start = 0
			else:
				start = key.start
		else:
			start = key

		if isinstance(key, slice):
			if key.stop is None:
				stop = self.size
			else:
				stop = key.stop
		else:
			stop = start + 1
		stop = min(stop, self.size)

		assert key.step is None
		return start, stop

	def _row_stat(self, line):
		''' Uses some heuristics to determine the length of sequence lines.
		
		    @return: a tuple with:
                      - the line length
                      - the line terminator length
		'''
		line_len = len(line)
		
		line_pos = line_len - 1
		while line_pos >= 0 and line[line_pos] in '\r\n':
			line_pos -= 1
		
		if line_pos <= 0:
			raise ValueError, 'first content line of FASTA file %s is empty' % self.filename

		return line_len, line_len - 1 - line_pos

	def _convert_range(self, line_len, newline_len, start, stop):
		''' Converts a range from sequence to file coordinates.

		    @param line_len: the maximum content length for each line.
		    @param newline_len: the line terminator length.
		    @param start: the range start.
		    @param stop: the range stop.
		    @return: the converted (start, stop) range.
		'''
		content_per_line = line_len - newline_len
		rows = start / content_per_line
		excess = start % content_per_line
		fasta_start = rows * line_len + excess

		rows = stop / content_per_line
		excess = stop % content_per_line
		fasta_stop = rows * line_len + excess

		return fasta_start, fasta_stop


class SingleBlockReader(RandomAccessSequence):
	''' Reader optimized for files containing a single sequence.
	
	    This class exposes the following properties:
	      - B{filename}: the path of the FASTA file, as given to the class
	                     constructor;
	      - B{force_lower}: wheter the reader is forcing all symbols to lower
	                        case.
	      - B{header}: the text of the FASTA header (the initial '>' is stripped);
	      - B{size}: the length of the sequence.
	'''
	
	def __init__(self, filename, force_lower=False):
		''' Object constructor. 
		
		    @param filename: the path of the file to read.
		    @param force_lower: wheter to force all symbols to lower case.
		    @raises FormatError: if the FASTA file is malformed.
		'''
		self.filename = filename
		
		self.fd = file(filename, 'r')
		self.header = self._read_header()
		self.content_start = self.fd.tell()
		self.line_len, self.newline_len = self._row_stat(self.fd.readline())
		self.size = self._get_size()
		self.sequence_filter = make_sequence_filter(force_lower, True)

	def close(self):
		''' Closes the reader. '''
		self.fd.close()
	
	def __getitem__(self, key):
		start, stop = self._key_to_range(key)
		if start >= self.size:
			return ''
		else:
			return self._get(start, stop)
	
	def get(self, start, size):
		''' Retrieves a slice of the sequence. 
		
		    @param start: the first position to read.
		    @param size: the size of the slice.
		    @return: the requested sub-sequence.
		    @raises ValueError: if one of I{start}, I{size} is out of range.
		'''
		if start < 0 or start >= self.size:
			raise ValueError, 'invalid start coordinate %d (content size %d)' % (start, self.size)
		
		stop = start + size
		if size < 0 or stop > self.size:
			raise ValueError, 'invalid size %d (sequence start is %d; sequence size is %d)' % (size, start, self.size)
		
		return self._get(start, stop)
	
	def _get(self, start, stop):
		start, stop = self._convert_range(self.line_len, self.newline_len, start, stop)
		self.fd.seek(self.content_start + start, SEEK_SET)
		return self.sequence_filter(self.fd.read(stop-start))
	
	def _read_header(self):
		''' Reads the FASTA header on the first line of the file.
		
		    @return: the header, with '>' stripped.
		    @raises FormatError: if the header is malformed.
		'''
		header = self.fd.readline()
		if len(header) == 0 or header[0] != '>':
			raise FormatError, 'malformed FASTA header'
		else:
			return header[1:].rstrip()
	
	def _get_size(self):
		''' Computes the sequence size.
		
		    @return: the size.
		'''
		file_size = fstat(self.fd.fileno()).st_size - self.content_start
		row_num = file_size / self.line_len
		excess = file_size % self.line_len
		return (row_num * (self.line_len - self.newline_len)) + max(excess - self.newline_len, 0)

class MultipleBlockReader(RandomAccessSequence):
	def __init__(self, filename, force_lower=False, index=None):
		self.filename = filename
		self.sequence_filter = make_sequence_filter(force_lower, True)
		
		self.fd = None
		self.mf = None
		self._open_map()
		try:
			if index:
				self._load_index(index)
			else:
				self._build_index()

			self.line_len, self.newline_len = self._load_row_stat()
		except:
			self.close()
			raise
	
	def __del__(self):
		self.close()
	
	def __len__(self):
		return len(self.block_list)
	
	def __getitem__(self, key):
		if type(key) == IntType:
			return Block(self, key, *self.block_list[key][1:])
		else:
			return Block(self, key, *self.block_map[key])
	
	def close(self):
		if self.mf is not None:
			self.mf.close()
			self.mf = None
		if self.fd is not None:
			self.fd.close()
			self.fd = None
	
	def blocks(self):
		return [ s[0] for s in self.block_list ]
	
	def iter_blocks(self):
		for label, size, start, bytes in self.block_list:
			yield Block(self, label, size, start, bytes)
	
	def _open_map(self):
		self.fd = file(self.filename, 'r')
		self.file_size = fstat(self.fd.fileno()).st_size
		
		self.mf = None
		if self.file_size == 0:
			raise ValueError, 'file %s is empty' % self.filename

		try:
			self.mf = mmap(self.fd.fileno(), self.file_size, access=ACCESS_READ)
		except:
			self.fd.close()
			raise
	
	def _load_index(self, filename):
		self.block_list = []
		self.block_map = {}
		
		with file(filename, 'r') as fd:
			reader = Reader(fd, '0s,1u,2u,3u', False)
			while True:
				record = reader.readline()
				if record is None:
					break
				else:
					# record[2] represents the offset of the FASTA header.
					# To obtain the offset of the corresponding sequence we
					# add the length of the label plus 2 (one for the heading '>'
					# and another for the trailing \n)
					delta = len(record[0]) + 2
					start = record[2] + delta
					bytes = record[3] - delta
					self.block_list.append( (record[0], record[1], start, bytes) )
					self.block_map[record[0]] = (record[1], start, bytes)
	
	def _build_index(self):
		self.block_list = []
		self.block_map = {}

		if self.mf[0] != '>':
			raise ValueError, 'invalid first char of FASTA file'
		
		pos = 0
		header = None
		start = 0
		size = 0
		while True:
			line_end = self.mf.find('\n', pos)
			if line_end == -1:
				size += self.file_size - pos
				break
			else:
				if self.mf[pos] == '>':
					if header:
						self.block_list.append((header, size, start, pos-start-1))
						self.block_map[header] = (size, start, pos-start-1)
					header = self.mf[pos+1:line_end]
					start = line_end + 1
					size = 0
				else:
					size += line_end - pos
				
				pos = line_end + 1
		
		if header:
			self.block_list.append((header, size, start, pos-start-1))
			self.block_map[header] = (size, start, pos-start-1)

	def _load_row_stat(self):
		# find the longest line in the first 100
		pos = 0
		for i in xrange(100):
			new_pos = self.mf.find('\n', pos)
			if new_pos == -1: break
			pos = new_pos+1

		return max(self._row_stat(l+'\n') for l in self.mf[:pos].split('\n') if len(l) and l[0] != '>')

	def _convert_range(self, start, stop):
		return RandomAccessSequence._convert_range(self, self.line_len, self.newline_len, start, stop)

class Block(RandomAccessSequence):
	def __init__(self, parent, label, size, start, bytes):
		self._parent = parent
		self.label = label
		self.size = size
		self.segment_offset = start
		self.bytes = bytes
	
	def __getitem__(self, key):
		start, stop = self._parent._convert_range(*self._key_to_range(key))
		start += self.segment_offset
		stop  += self.segment_offset
		return self._parent.sequence_filter(self._parent.mf[start:stop])
	
	def raw_content(self):
		start = self.segment_offset
		stop = self.segment_offset + self.bytes
		return self._parent.mf[start:stop]


class MultipleBlockStreamingReader(object):
	''' A sequential reader.

            May be used with FASTA files whose blocks contain arbitrary content.
	'''

	def __init__(self, src, join_lines=True, force_lower=False):
		''' Object constructor. 
		
		    @param src: the path of the file to read or a file descriptor.
		    @param join_lines: whether to join all the lines in each block.
		    @param force_lower: whether to force all symbols to lower case.
		'''
		self.join_lines = join_lines
		self.sequence_filter = make_sequence_filter(force_lower, False)
		
		if type(src) in StringTypes:
			self.filename = src
			self.fd = file(src, 'r')
		else:
			self.filename = None
			self.fd = src
	
	def __iter__(self):
		''' Provides an iterator over FASTA blocks.
		
		    @return: if C{join_lines} is B{True} an (header, sequence) tuple
		             for each block. Otherwise an (header, line iterator) pair
		             for each block.
		    @raises FormatError: if the FASTA file is malformed
		'''
		self.lineno = 0
		self.header = self._first_header()
		
		while self.header is not None:
			current_header = self.header
			it = self._iter_block()
			
			if self.join_lines:
				content = StringIO()
				for line in it: content.write(line)
				yield current_header, content.getvalue()
			else:
				yield current_header, it
				for line in it: pass
	
	def _first_header(self):
		line = self.fd.readline()
		if len(line) == 0:
			return None
		self.lineno += 1
	
		line = safe_rstrip(line)
		if len(line) == 0:
			raise FormatError, self._error_msg('unexpected empty row', self.lineno)
		elif line[0] != '>':
			raise FormatError, self._error_msg('missing FASTA header', self.lineno)
		else:
			return line[1:]
		
	def _iter_block(self):
		for line in self.fd:
			self.lineno += 1
			
			line = safe_rstrip(line)
			if len(line) == 0:
				raise FormatError, self._error_msg('unexpected empty row', self.lineno)
			elif line[0] == '>':
				self.header = line[1:]
				if len(self.header) == 0:
					raise FormatError, self._error_msg('empty FASTA header', self.lineno)
				return
			else:
				yield self.sequence_filter(line)
		
		self.header = None
	
	def _error_msg(self, msg, lineno):
		if self.filename is None:
			return '%s at line %d' % (msg, lineno+1)
		else:
			return '%s at line %d of file %s' % (msg, lineno+1, self.filename)

class StreamingBlock(object):
	def __init__(self):
		self.content = []
	
	def append(self, data):
		self.content.append(data)
	
	def get_content(self):
		return self.content

class StreamingJoinedBlock(object):
	def __init__(self):
		self.content = StringIO()
	
	def append(self, data):
		self.content.write(data)
	
	def get_content(self):
		return self.content.getvalue()

class FormatError(Exception):
	''' Raised to signal an error in the format of a FASTA file. '''
