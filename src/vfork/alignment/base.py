''' Base tools for representing and handling alignments. '''
from cStringIO import StringIO
from itertools import izip
from ..sequence import reverse_complement
from ..fasta.reader import RandomAccessSequence

class Alignment(object):
	''' A container for the details of a single alignment.
	
	    It exposes the following properties:
	      - query_label
	      - query_start
	      - query_stop
	      - target_label
	      - target_start
	      - target_stop
	      - strand
	      - frame
	      - length
	      - score
	      - identity
	      - evalue
	      - query_gaps
	      - target_gaps
	      - group
	      - links
	      - sum
	'''
	
	__slots__ = (
		'query_label',
		'query_start',
		'query_stop',
		'target_label',
		'target_start',
		'target_stop',
		'strand',
		'frame',
		'length',
		'score',
		'identity',
		'evalue',
		'query_gaps',
		'target_gaps',
		'group',
		'links',
		'sum'
	)
	
	def __init__(self, *args):
		''' Object constructor.
		
		    @param args: a list of values used to initialize fields.
		    @raises ValueError: if *args contains too many values.
		'''
		if len(args) > len(self.__slots__):
			raise ValueError, 'too many positional arguments'
		
		for attr, value in zip(self.__slots__, args):
			setattr(self, attr, value)
		
		for attr in self.__slots__[len(args):]:
			setattr(self, attr, None)
	
	def __eq__(self, other):
		for attr in self.__slots__:
			if getattr(self, attr) != getattr(other, attr):
				return False
		return True
	
	def __str__(self):
		t = []
		for attr in self.__slots__:
			t.append('% 15s: %s' % (attr, str(getattr(self, attr))))
		return '\n'.join(t)
	
	def __repr__(self):
		return self.__str__()

class AlignedSequences(object):
	''' This class represents two aligned sequences.
	
	    It exposes the following properties:
	      - B{alignment}: an L{Alignment} instance;
	      - B{query_sequence}: a string holding the query sequence;
	      - B{target_size}: a string holding the target sequence;
	      - B{aligned_sequences}: a list of 3 strings containing the aligned
	                              query sequence, the match markers and
	                              the aligned target sequence.
	'''
	
	def __init__(self, alignment, query, target):
		''' Extracts the aligned sequences from I{query} and I{target} and
		    process them.
		
		    @param alignment: an L{Alignment} instance.
		    @param query: a L{RandomAccessSequence} instance.
		    @param target: a L{RandomAccessSequence} instance.
		    @raises IndexError: if the aligned sequence is outside either
		                        B{query} or B{target}.
		'''
		if alignment.query_stop - alignment.query_start + self._cumulative_gap_size(alignment.query_gaps) != \
		   alignment.target_stop - alignment.target_start + self._cumulative_gap_size(alignment.target_gaps):
			raise ValueError, 'mismatch between aligned query and target lengths'
		
		self.alignment = alignment
		self.query_sequence = query[alignment.query_start:alignment.query_stop]
		self.target_sequence = target[alignment.target_start:alignment.target_stop]
		
		aligned_query_sequence = self._insert_gaps(self.query_sequence, alignment.query_gaps)
		aligned_target_sequence = self._insert_gaps(reverse_complement(self.target_sequence) if alignment.strand == '-' else self.target_sequence, alignment.target_gaps)
		self.aligned_sequences = [ aligned_query_sequence, self._match_marks(aligned_query_sequence, aligned_target_sequence), aligned_target_sequence ]
	
	def display(self, fd, width, format='text'):
		''' Formats B{aligned_sequences} for display.
		    Each produced row is shorter than I{width} characters. 
		
		    @param fd: a file-object to write to.
		    @param width: the maximum row length.
		    @param format: the type of output. Right now only 'text' is supported.
		    @return: a string.
		'''
		if format != 'text':
			raise ValueError, 'unsupported format'
		
		print >>fd, 'QUERY:  %s, %d-%d' % (self.alignment.query_label, self.alignment.query_start, self.alignment.query_stop)
		print >>fd, 'TARGET: %s, %d-%d' % (self.alignment.target_label, self.alignment.target_start, self.alignment.target_stop)
		
		query, marks, target = self.aligned_sequences
		while len(query):
			print >>fd
			print >>fd, query[:width]
			print >>fd, marks[:width]
			print >>fd, target[:width]
			print >>fd, ''
			
			query = query[width:]
			marks = marks[width:]
			target = target[width:]
	
	def _cumulative_gap_size(self, gaps):
		return sum(g[1] for g in gaps)
	
	def _insert_gaps(self, sequence, gaps):
		start = 0
		out = []
		
		for gap_start, gap_length in gaps:
			assert gap_start >= start, 'disorder found in gaps: %s' % repr(gaps)
			out.append(sequence[start:gap_start])
			out.append('-'*gap_length)
			start = gap_start
		
		out.append(sequence[start:])
		return ''.join(out)
	
	def _match_marks(self, query, target):
		return ''.join(('|' if q == t != '-' else ' ') for q,t in izip(query, target))
