__author__ = "Gabriele Sales <gbrsales@gmail.com>"
__copyright__ = "2009-2010 Gabriele Sales"

from shutil import rmtree
from tempfile import mkdtemp
from ..util import exit


class NamedTemporaryDirectory(object):
	''' A temporary directory whose content will be automatically deleted.

            The returned object is meant to be used in a B{with} statement.
	'''

	def __init__(self, dir=None):
		''' Object constructor.

		    @param dir: where to create the temporary directory.
		'''
		self._dir = dir

	def __enter__(self):
		self.path = mkdtemp(dir=self._dir)
		return self

	def __exit__(self, type, value, traceback):
		rmtree(self.path, ignore_errors=True)


def safe_rstrip(line):
	''' Performs a right strip of the line, without loosing
	    any (possibly empty) column.

	    @param line: input line.
	    @return: the stripped line.
	'''
	return line.rstrip('\r\n')


def parse_int(s, name, check=None):
	''' Parses an int literal, possibly performing range checks.

	    If a check fails, exits from the app printing a description
	    of the error.

	    @param s: the literal.
	    @param name: a name for the literal (used for error messages).
	    @param check: one of None (no checks), 'positive' (>=0) or
	                  'strict_positive' (>0).
	    @return: the parsed value.
	'''
	if check not in (None, 'positive', 'strict_positive'):
		raise ValueError, 'invalid check'

	try:
		v = int(s)
		if check == 'positive':
			if v < 0: raise ValueError
		elif check == 'strict_positive':
			if v <=0: raise ValueError
		return v
	except ValueError:
		exit('Invalid %s: %s' % (name, s))

def parse_float(s, name, check=None):
	''' Parses an float literal, possibly checking if it's positive.

	    If a check fails, exits from the app printing a description
	    of the error.

	    @param s: the literal.
	    @param name: a name for the literal (used for error messages).
	    @param check: one of None (no checks), 'positive' (>=0) or
	                  'strict_positive' (>0).
	    @return: the parsed value.
	'''
	if check not in (None, 'positive', 'strict_positive'):
		raise ValueError, 'invalid check'

	try:
		v = float(s)
		if check == 'positive':
			if v < 0: raise ValueError
		elif check == 'strict_positive':
			if v <=0: raise ValueError
		return v
	except ValueError:
		exit('Invalid %s: %s' % (name, s))
