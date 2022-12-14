from os import linesep


# DEPRECATED
class SingleBlockWriter(object):
	def __init__(self, f, header, width=80):
		if type('') is type(f):
			self.fd = file(f, 'w')
		else:
			self.fd = f

		self.write_header(header)
		self.width = width
		self.pending = ''

	def close(self):
		print(self.pending, file=self.fd)
		self.pending = ''
		self.fd.close()

	def write(self, seq):
		self.pending += seq

		content_width = self.width - len(linesep)
		while len(self.pending) >= content_width:
			line = self.pending[:content_width]
			self.pending = self.pending[content_width:]
			print(line, file=self.fd)

	##
	## Internal use only
	##
	def write_header(self, header):
		if header[0] != '>':
			header = '>' + header
		print(header, file=self.fd)

class MultipleBlockWriter(object):
	def __init__(self, f, max_width=80):
		self.max_width = max_width
		self.sequence_buffer = ''
		self._open_file(f)

	def flush(self):
		if len(self.sequence_buffer) > 0:
			print(self.sequence_buffer, file=self.fd)
			self.sequence_buffer = ''

	def write_header(self, header):
		self.flush()
		print('>%s' % header, file=self.fd)

	def write_sequence(self, sequence):
		self.sequence_buffer += sequence

		last_offset = len(self.sequence_buffer) // self.max_width * self.max_width
		for offset in range(0, last_offset, self.max_width):
			print(self.sequence_buffer[offset:offset+self.max_width], file=self.fd)

		if last_offset > 0:
			self.sequence_buffer = self.sequence_buffer[last_offset:]

	def _open_file(self, f):
		if isinstance(f, str) or isinstance(f, bytes):
			self.fd = file(f, 'w')
		else:
			self.fd = f
