from __future__ import with_statement
from cStringIO import StringIO
from types import StringTypes

class RecordIterator(object):
	''' An iterator over GenBank-formatted records. '''

	def __init__(self, src):
		''' Builds an iterator.
		    
		    @param src: the path of the file to read or a file descriptor.
		'''
		if type(src) in StringTypes:
			self.fd = file(src, 'r')
			self.need_close = True
		else:
			self.fd = src
			self.need_close = False
	
	def __del__(self):
		if self.need_close:
			self.fd.close()

	def __iter__(self):
		while True:
			record = StringIO()
			for line in self.fd:
				record.write(line)
				if self._is_separator(line):
					break
				
			record = record.getvalue()
			if len(record) == 0:
				break
				
			yield record
	
	def _is_separator(self, line):
		return line.strip() == '//'
