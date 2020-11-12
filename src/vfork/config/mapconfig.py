from sys import stderr

class Configuration(object):
	'''
	This class provides access to I{(key,value)} pairs stored
	in plain text files.
	
	It expects the following format::
	    	
	   #comment
	   key: value
    	
	You can access values in a dictionary-like style:
    	
		>>> conf = Configuration().load('file.conf')
		>>> print conf['key']
		'value'
	    	
	or get a reference to a real dictionary using the 
	L{as_dict} method.
	'''
	
	def __init__(self):
		''' Builds a new L{Configuration} instance. '''
		self.options = {}
	
	def load(self, filename):
		''' Loads configuration values from a file.
		
		    @param filename: the file to read.
		    @return: a reference to this instance.
		'''
		self.options = {}
		
		fd = file(filename, 'r')
		for lineno, line in enumerate(fd):
			line = line.strip()
			if len(line) == 0 or line[0] == '#':
				continue
			
			try:
				key, value = line.split(':', 2)
				key = key.strip()
				if len(key) == 0:
					raise ValueError
				
				value = value.strip()
				self.options[key] = value
			
			except ValueError:
				print >>stderr, 'WARNING: malformed option at line %d; skipping' % (lineno+1)
				continue
		
		fd.close()
		return self
	
	def as_dict(self):
		''' Provides a dictionary exposing configuration values.
		
		    @return: a dictionary.
		'''
		return self.options.copy()
	
	def __getitem__(self, key):
		''' Dictionary-like access to configuration values.
		
		    @param key: the configuration key.
		    @return: the corresponding value.
		    @raises KeyError: if I{key} wasn't found.
		'''
		return self.options[key]
