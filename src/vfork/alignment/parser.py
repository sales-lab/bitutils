''' Parsers for the output of various alignment tools. '''

from .base import Alignment
from os import linesep
import re

# WARNINGS
from sys import stderr

class LalignParser(object):
	''' A parser for LALIGN output.
	
	    Usage example:
	      >>> parser = LalignParser()
	      >>> for alignment in parser.parse(stdin):
	      ...     print alignment.quert_start, alignment.query_stop	
	'''
	
	def __init__(self):
		''' Object constructor. '''
		self.header_rx = re.compile(r'\s*Comparison of:')
		self.summary_rx = re.compile(r'\s*(\d+\.\d+)% identity in (\d+) nt overlap \((\d+)-(\d+):(\d+)-(\d+)\); score:\s+(\d+) E\(\d+\):\s+(\d+(:?\.\d+)?(:?e[+-]\d+)?)')
		self.query_len = None
		self.strand = None
	
	def parse(self, fd):
		''' Parses the output of LALIGN.
		
		    @param fd: a file-like object.
		    @return: an iterator over L{Alignment} instances.
		    @raises ParseError: when the parser cannot interpret the text.
		'''
		rw = RowWrapper(fd)
		self.query_label = None
		self.target_label = None

		try:
			while True:
				line = rw.readline('', maybe_eof=True)

				m = self.header_rx.match(line)
				is_header = m is not None
				if is_header:
					self._parse_header(rw)
				else:
					rw.unread(line)

				alignment = self._parse_alignment(rw)
				if alignment is not None:
					yield alignment
				elif not is_header:
					raise ParseError('unexpected content at line %d' % rw.lineno)

		except EOFError:
			pass

	##
	## Internal use only
	##
	def _parse_header(self, rw):
		''' Parses the alignment header.
		
		    @param rw: a L{RowWrapper} instance.
		    @raises ParseError: when the parser cannot interpret the text.
		'''
		for beginning, attr in (('(A)', 'query_label'), ('(B)', 'target_label')):
			line = rw.readline('was expecting an header')
			tokens = line.split()
			if tokens[0] != beginning:
				raise ParseError('unexpected header at line %d' % rw.lineno)
			else:
				if tokens[2] == '(rev-comp)':
					setattr(self, attr, tokens[3])
					self.strand = '-'
					
					try:
						self.query_len = int(tokens[-2])
					except ValueError:
						raise ParseError('invalid query length at line %d' % rw.lineno)
				
				else:
					setattr(self, attr, tokens[2])
					if beginning == '(A)':
						self.strand = '+'
	
		line = rw.readline('was expecting an header')
		if not line.startswith(' using matrix file:'):
			raise ParseError('unexpected header at line %d' % rw.lineno)

	def _parse_alignment(self, rw):
		''' Parses the description of an alignment.
		
		    @param rw: a L{RowWrapper} instance.
		    @return: an L{Alignment} instance.
		    @raises ParseError: when the parser cannot interpret the text.
		'''
		line = rw.readline('', maybe_eof=True)
		m = self.summary_rx.match(line)
		if m is None:
			rw.unread(line)
			return None
		
		alignment = Alignment()
		alignment.query_label = self.query_label
		alignment.target_label = self.target_label
		alignment.identity = float(m.group(1))
		alignment.length = int(m.group(2))
		alignment.strand = self.strand
		alignment.score = int(m.group(7))
		alignment.evalue = float(m.group(8))
		
		alignment.query_start = int(m.group(3)) - 1
		alignment.query_stop = int(m.group(4))
		if self.strand == '-':
			alignment.query_start, alignment.query_stop = self.query_len - alignment.query_stop, self.query_len - alignment.query_start
		
		alignment.target_start = int(m.group(5)) - 1
		alignment.target_stop = int(m.group(6))
		
		self._parse_strand_gaps(rw, alignment)
		return alignment
		
	def _parse_strand_gaps(self, rw, alignment):
		''' Determines the strand of the aligned sequence and builds a list
		    of the gaps.
		
		    @param rw: a L{RowWrapper} instance.
		    @param alignment: an L{Alignment} instance.
		    @raises ParseError: when the parser cannot interpret the text.
		'''
		query_gap_scanner = GapScanner()
		target_gap_scanner = GapScanner()
		
		while True:
			line = rw.readline('was expecting alignment details')
			if line[0] == '-':
				break
						
			details = [ rw.readline('was expecting alignment details') for i in range(4) ]
			
			idx = details[0].find(' ')
			if idx == -1:
				raise ParseError('unexpected alignment details at line %d' % rw.lineno)
			query_gap_scanner.feed(details[0][idx+1:].strip())
			
			idx = details[2].find(' ')
			if idx == -1:
				raise ParseError('unexpected alignment details at line %d' % rw.lineno)
			target_gap_scanner.feed(details[2][idx+1:].strip())
		
		alignment.query_gaps = query_gap_scanner.finalize()
		alignment.target_gaps = target_gap_scanner.finalize()

class WuBlastParser(object):
	''' A parser for WU BLAST output.
	
	    Usage example:
	      >>> parser = WuBlastParser()
	      >>> for alignment in parser.parse(stdin):
	      ...     print alignment.quert_start, alignment.query_stop	
	'''
	
	def __init__(self):
		''' Object constructor. '''
		self.query_label_rx = re.compile(r'Query=\s*([^\s]+)')
		self.target_label_rx = re.compile(r'>([^\s]+)')
		self.plus_strand_label = 'Plus Strand HSPs:'
		self.minus_strand_label = 'Minus Strand HSPs:'
		self.header1_rx = re.compile(r'\s*Score = (\d+) \([^\)]+\), Expect = ([^,]+)')
		self.group_rx = re.compile(r'Group = (\d+)')
		self.links_rx = re.compile(r'\s*Links = (.+)')
		self.header2_rx = re.compile(r'\s*Identities = \d+/\d+ \((\d+)%\), Positives = \d+/\d+ \(\d+%\), (?:Strand = (Plus|Minus) / Plus|Frame = ([+-]\d+))')
		self.query_rx = re.compile(r'Query:\s+(\d+)\s+([^\s]+)\s+(\d+)')
		self.subject_rx = re.compile(r'Sbjct:\s+(\d+)\s+([^\s]+)\s+(\d+)')
	
	def parse(self, fd):
		''' Parses the output of WU BLAST.
		
		    @param fd: a file-like object.
		    @return: an iterator over L{Alignment} instances.
		    @raises ParseError: when the parser cannot interpret the text.
		'''
		rw = RowWrapper(fd)
		self.query_label = None
		self.target_label = None
		self.strand = '+'
		
		try:
			while True:
				line = rw.readline('', maybe_eof=True)
				
				if self.plus_strand_label in line:
					self.strand = '+'
				
				elif self.minus_strand_label in line:
					self.strand = '-'
				
				else:
					m = self.header1_rx.match(line)
					if m is not None:
						assert self.query_label is not None, 'missing query label at line %d' % rw.lineno
						assert self.target_label is not None, 'missing target label at line %d' % rw.lineno
						
						alignment = Alignment()
						alignment.query_label = self.query_label
						alignment.target_label = self.target_label
						alignment.score = int(m.group(1))
						alignment.evalue = float(m.group(2))
						
						m = self.group_rx.search(line[m.end():])
						if m is not None:
							alignment.group = int(m.group(1))
						
						self._parse_alignment(rw, alignment)
						yield alignment
					
					else:
						m = self.query_label_rx.match(line)
						if m is not None:
							self.query_label = m.group(1)
							continue
						
						m = self.target_label_rx.match(line)
						if m is not None:
							self.target_label = m.group(1)
							continue
		
		except EOFError:
			pass
	
	##
	## Internal use only
	##
	def _parse_alignment(self, rw, alignment):
		''' Parses the textual alignment description.
		
		    @param rw: a L{RowWrapper} instance.
		    @param alignment: an L{Alignment} instance.
		    @raises ParseError: when the parser cannot interpret the text.
		'''
		line = rw.readline('was expecting second line of alignment header')
		
		m = self.header2_rx.match(line)
		if m is None:
			raise ParseError('was expecting second line of alignment header at line %d' % rw.lineno)
		
		alignment.identity = int(m.group(1))
		
		strand = m.group(2)
		if strand:
			alignment.frame = None
			if strand == 'Plus':
				alignment.strand = '+'
			elif strand == 'Minus':
				alignment.strand = '-'
			else:
				raise ParseError('unexpected strand name at line %d' % rw.lineno)
			
			assert alignment.strand == self.strand, 'unexpected strand %s at line %d (according to the preceding header strand is %s)' % (alignment.strand, rw.lineno, self.strand)
		else:
			alignment.strand = self.strand
			alignment.frame = int(m.group(3))
		
		line = rw.readline('was expecting alignment details')
		m = self.links_rx.match(line)
		if m:
			alignment.links = m.group(1)
			line = None
		
		self._parse_details(line, rw, alignment)
	
	def _parse_details(self, first_line, rw, alignment):
		''' Parses the details of the aligned sequences.
		
		    @param first_line: the first line of alignment details, possibly B{None}.
		    @param rw: a L{RowWrapper} instance.
		    @param alignment: an L{Alignment} instance.
		    @raises ParseError: when the parser cannot interpret the text.
		'''
		query_start = None
		target_start = None
		query_gap_scanner = GapScanner()
		target_gap_scanner = GapScanner()
		length = 0
		
		while True:
			if first_line:
				line = first_line
				first_line = None
			else:
				line = rw.readline('was expecting query details')
			
			m = self.query_rx.match(line)
			if m is None:
				rw.unread(line)
				break
			
			if query_start is None:
				query_start = int(m.group(1))
			
			seq = m.group(2)
			length += len(seq)
			query_gap_scanner.feed(seq)
			query_stop = m.group(3)
			
			rw.readline('was expecting alignment details')
			
			line = rw.readline('was expecting target details')
			m = self.subject_rx.match(line)
			if m is None:
				raise ParseError('was expecting target details at line %d' % rw.lineno)
			
			if target_start is None:
				target_start = int(m.group(1)) - 1
			
			target_gap_scanner.feed(m.group(2))
			target_stop = m.group(3)
		
		if query_start is None:
			raise ParseError('was expecting alignment details at line %d' % rw.lineno)
		
		query_stop = int(query_stop)
		if alignment.strand == '+':
			alignment.query_start = query_start - 1
			alignment.query_stop = query_stop
		elif alignment.strand == '-':
			alignment.query_start = query_stop - 1
			alignment.query_stop = query_start
		
		alignment.target_start = target_start
		alignment.target_stop = int(target_stop)
		alignment.length = length
		alignment.query_gaps = query_gap_scanner.finalize()
		alignment.target_gaps = target_gap_scanner.finalize()
		
		assert alignment.query_start < alignment.query_stop, 'alignment.query_start (%d) >= alignment.query_stop (%d) before line %d' % (alignment.query_start, alignment.query_stop, rw.lineno)
		assert alignment.target_start < alignment.target_stop, 'alignment.target_start (%d) >= alignment.target_stop (%d) before line %d' % (alignment.target_start, alignment.target_stop, rw.lineno)

class BlastzParser(object):
	''' A parser for BLASTZ output.
	
	    Usage example:
	      >>> parser = BlastzParser()
	      >>> for alignment in parser.parse(stdin):
	      ...     print alignment.quert_start, alignment.query_stop	
	'''

	def __init__(self, max_gap=10):
		''' Object constructor.
		
		    @param max_gap: spit alignments having gaps larger than I{max_gap}.
		'''
		self.max_gap = max_gap
		self.query_label = None
		self.target_label = None
		self.target_sequence_length = None
		self.strand = None
		self.traceback = None

		print >>stderr, '[WARNING] BlastzParser is beta quality.'
		
	def parse(self, fd):
		''' Parses the output of BLASTZ.
		
		    @param fd: a file-like object.
		    @return: an iterator over L{Alignment} instances.
		    @raises ParseError: when the parser cannot interpret the text.
		'''
		self.rw = RowWrapper(fd)
		try:
			while True:
				line = self.rw.readline('', maybe_eof=True)
				if line.startswith('s {'):
					self._parse_sequence_info()
				
				elif line.startswith('h {'):
					self._parse_header()
				
				elif line.startswith('a {'):
					if self.query_label is None:
						raise ParseError(
							'found alignment details at line %d, but was expecting an header' % self.rw.lineno)
					else:
						self._skip_alignment_header()
						
						while True:
							alignment = self._parse_alignment()
							if alignment is None:
								break
							else:
								yield alignment
				
		except EOFError:
			pass
	
	def _parse_sequence_info(self):
		self.rw.readline('was expecting query sequence informations')
		
		try:
			info_str = self.rw.readline('was expecting target sequence informations')
			pos = info_str.rfind('"')
			if pos == -1:
				raise ValueError
		
			tokens = info_str[pos+1:].split(None)
			if len(tokens) != 4:
				raise ValueError
			
			self.target_sequence_length = int(tokens[1])
		
		except ValueError:
			raise ParseError('malformed target sequence informations at line %d' % self.rw.lineno)
	
	def _parse_header(self):
		self.query_label = self._read_label('query')
		
		rev_label = ' (reverse complement)'
		target_label = self._read_label('target')
		if target_label.endswith(rev_label):
			self.strand = '-'
			target_label = target_label[:-len(rev_label)]
		else:
			self.strand = '+'
		self.target_label = target_label
		
		if not self.rw.readline('was expecting header end mark').startswith('}'):
			raise ParseError('was expecting header end mark at line %d' % self.rw.lineno)
	
	def _read_label(self, name):
		label = self.rw.readline('was expecting %s label' % name)
		return label.strip().replace('"', '')[1:]
	
	def _skip_alignment_header(self):
		while True:
			tokens = self.rw.readline('was expecting alignment header').split(None)
			if tokens[0] not in 'sbe':
				self.traceback = tokens
				break
	
	def _parse_alignment(self):
		alignment = None
		
		while True:
			if self.traceback is None:
				tokens = self.rw.readline('was expecting alignment details').split(None)
			else:
				tokens = self.traceback
				self.traceback = None
			
			if tokens[0] == 'l':
				try:
					query_start = int(tokens[1]) - 1
					target_start = int(tokens[2]) - 1
					query_stop = int(tokens[3])
					target_stop = int(tokens[4])
					score = int(tokens[5])
				except ValueError:
					raise ParseError('invalid HSP at line %d' % self.rw.lineno)
				
				# meaningless lines force the output of the alignment
				if query_start == query_stop or target_start == target_stop:
					if alignment is not None:
						return self._fix_alignment(alignment)
					else:
						continue
				
				if alignment is None:
					alignment = self._init_alignment()
					alignment.query_start = query_start
					alignment.target_start = target_start
					alignment.query_stop = query_stop
					alignment.target_stop = target_stop
					alignment.length = query_stop - query_start
				
				else:
					query_skip_len = query_start - alignment.query_stop
					target_skip_len = target_start - alignment.target_stop
					assert not (query_skip_len > 0 and target_skip_len > 0), 'gaps on both the query and the target at line %d' % self.rw.lineno
					
					if query_skip_len <= self.max_gap and target_skip_len <= self.max_gap and \
					   not (self._is_overlapped(alignment.query_start, alignment.query_stop, query_start, query_stop) or \
					        self._is_overlapped(alignment.target_start, alignment.target_stop, target_start, target_stop)):
						if query_skip_len > 0:
							alignment.target_gaps.append((alignment.length, query_skip_len))
							alignment.length += query_skip_len
						
						if target_skip_len > 0:
							alignment.query_gaps.append((alignment.length, target_skip_len))
							alignment.length += target_skip_len
						
						alignment.query_stop = query_stop
						alignment.target_stop = target_stop
						alignment.length += query_stop - query_start
					
					else:
						self.traceback = tokens
						return self._fix_alignment(alignment)
			
			elif tokens[0] == '}':
				if alignment is not None:
					self.traceback = tokens
					return self._fix_alignment(alignment)
				else:
					break
			
			else:
				raise ParseError('unexpected field at line %d' % self.rw.lineno)
		
		return None
	
	def _init_alignment(self):
		alignment = Alignment()
		alignment.query_label = self.query_label
		alignment.target_label = self.target_label
		alignment.strand = self.strand
		alignment.query_gaps = []
		alignment.target_gaps = []
		return alignment
	
	def _is_overlapped(self, start1, stop1, start2, stop2):
		return not (stop1 <= start2 or stop2 <= start1)
	
	def _fix_alignment(self, alignment):
		if self.strand == '-':
			alignment.target_start = self.target_sequence_length - alignment.target_stop
			alignment.target_stop  = self.target_sequence_length - alignment.target_start
		return alignment
	
class RowWrapper(object):
	''' A wrapper on a file-like object automatically skipping blank lines and 
	    keeping track of row numbers.
	'''
	
	def __init__(self, fd):
		''' Object constructor.
		
		    @param fd: a file-like object.
		'''
		self.lineno = 0
		self.fd = fd
		self.traceback = None
	
	def readline(self, error_msg, maybe_eof=False):
		''' Reads the first non-blank line.
		
		    @param error_msg: the error message to attach to the
		                      L{ParseError} if it's raised.
		    @return: a line of text.
		    @raises ParseError: if EOF is encountered.
		'''
		while True:
			if self.traceback is None:
				line = self.fd.readline()
			else:
				line = self.traceback
				self.traceback = None
			
			if len(line) == 0:
				if maybe_eof:
					raise EOFError
				else:
					raise ParseError('%s at line %d' % (error_msg, self.lineno))
				
			self.lineno += 1
			if line != linesep:
				return line
	
	def unread(self, line):
		self.lineno -= 1
		self.traceback = line

class GapScanner(object):
	''' This scanner takes the textual representation of one of the sequences
	    making an alignment and builds a list of gaps.
	
	    Usage example:
	      >>> gs = GapScanner()
	      >>> gs.feed('AC--GT')
	      >>> gs.finalize()
	      [(2,2)]
	'''
	
	def __init__(self):
		''' Object constructor. '''
		self.pos = 0
		self.gap_open = None
		self.gaps = []
		self.gap_rx = re.compile(r'[-]+')
	
	def feed(self, seq):
		''' Feeds the scanner with the aligned sequence.
		
		    @param seq: (part of) the aligned sequence.
		'''
		if self.gap_open is not None and len(seq) > 0 and seq[0] != '-':
			self.gaps.append((self.gap_open, self.pos - self.gap_open))
			self.gap_open = None
		
		for m in self.gap_rx.finditer(seq):
			if m.end() != len(seq):
				if self.gap_open is not None:
					self.gaps.append((self.gap_open, m.end() + self.pos - self.gap_open))
					self.gap_open = None
				else:
					self.gaps.append((m.start() + self.pos, m.end() - m.start()))
			elif self.gap_open is None:
				self.gap_open = m.start() + self.pos
			
		self.pos += len(seq)
	
	def finalize(self):
		''' Ends the scan and returns the gap list.
		
		    @return: a list of tuples, each one containing the start coordinate
		             of a gap and its length.
		'''
		if self.gap_open is not None:
			self.gaps.append((self.gap_open, self.pos - self.gap_open))
			self.gap_open = None
		
		return self.gaps

class ParseError(Exception):
	''' Expception raised when a parser encounters an input it cannot
	    interpret.
	'''
