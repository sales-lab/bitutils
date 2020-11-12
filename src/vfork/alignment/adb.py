''' Tools to handle ADB files. '''
from .base import Alignment
from ..io.colreader import Reader

def _parse_gaps(gaps):
	res = []
	if len(gaps) == 0:
		return res
	
	for gap in gaps.split(';'):
		tokens = gap.split(',')
		if len(tokens) != 2:
			raise ValueError
		res.append((int(tokens[0]), int(tokens[1])))
	
	return res

def iter_alignments_simple(fd):
	''' Reads and (partially) parses alignments out of an ADB file.
	
	    @param fd: a file-like object.
	    @returns: an iterator over L{Alignment} instances with the folling fields filled in:
	      - query_label
	      - query_start
	      - query_stop
	      - target_label
	      - target_start
	      - target_stop
	      - strand
	      - length
	      - query_gaps
	      - target_gaps
	    @raises ValueError: if the input is invalid.
	'''
	reader = Reader(fd, '0s,1u,2u,3s,4s,5u,6u,7u,11s,12s', False)
	for qlabel, qstart, qstop, strand, tlabel, tstart, tstop, length, qgaps, tgaps in reader:
		if qstop <= qstart:
			raise ValueError, 'invalid query stop coordinate at line %d: %d' % (reader.lineno(), qstop)
		elif strand not in ('+', '-'):
			raise ValueError, 'invalid strand at line %d: %s' % (reader.lineno(), strand)
		elif tstop <= tstart:
			raise ValueError, 'invalid target stop coordinate at line %d: %d' % (reader.lineno(), tstop)
		
		try:
			qgaps = _parse_gaps(qgaps)
		except ValueError:
			raise ValueError, 'invalid query gaps at line %d: %s' % (reader.lineno(), qgaps)
		
		try:
			tgaps = _parse_gaps(tgaps)
		except ValueError:
			raise ValueError, 'invalid target gaps at line %d: %s' % (reader.lineno(), tgaps)
		
		yield Alignment(qlabel, qstart, qstop, \
		                tlabel, tstart, tstop, \
		                strand, None, length, None, None, None, qgaps, tgaps)
