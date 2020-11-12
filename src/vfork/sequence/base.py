''' Basic tools to handle genomic sequences. '''

def check_nucleotides(sequence):
	''' Check if a sequence contains only nucleotides. 
	
	    @param sequence: a string holding the sequence.
	    @return: a boolean.
	'''
	for n in sequence:
		if n not in 'ACGTNacgtn':
			return False
	return True
	

def _build_complement_table():
	tbl = [ chr(i) for i in xrange(256) ]
	for f, t in zip('ACGTNacgtn', 'TGCANtgcan'):
		tbl[ord(f)] = t
	return ''.join(tbl)
_COMPLEMENT_TABLE = _build_complement_table()

def complement(sequence):
	''' Computes the complement of the given sequence.

	    @param sequence: a string holding the sequence.
	    @return: a string holding the complement sequence.
	'''
	return sequence.translate(_COMPLEMENT_TABLE)

def reverse_complement(sequence):
	''' Computes the reverse complement of the given sequence. 
	
	    @param sequence: a string holding the sequence.
	    @return: a string holding the reverse complement sequence.
	'''
	return sequence[::-1].translate(_COMPLEMENT_TABLE)
	
def _build_lower_table():
	tbl = [ chr(i) for i in xrange(256) ]
	for c in 'ACGTN':
		tbl[ord(c)] = c.lower()
	return ''.join(tbl)
_LOWER_TABLE = _build_lower_table()
_NEUTRAL_TABLE = ''.join(chr(i) for i in xrange(256))

def make_sequence_filter(force_lower=False, strip_newlines=True):
	if force_lower == False and strip_newlines == False:
		return lambda s: s
	else:
		tbl = _LOWER_TABLE if force_lower else _NEUTRAL_TABLE
		strip_set = '\r\n' if strip_newlines else ''
		return lambda s: s.translate(tbl, strip_set)
