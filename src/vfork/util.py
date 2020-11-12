''' Utilities for scripts. '''

from __future__ import with_statement

__author__ = "Gabriele Sales <gbrsales@gmail.com>"
__copyright__ = "2005-2008,2014 Gabriele Sales"

import argparse
import errno
import os
import sys

def exit(message):
	''' Prints the name of the program being run and a message, then terminates the process.

	    @param message: the error message.
	'''
	sys.exit('[ERROR] %s: %s' % (sys.argv[0], message))

def format_usage(usage):
	''' Trims white-space from a multi-line literal string so that it doesn't introduce
	    visual artifacts when used as the I{usage} parameter of an OptionParser
	    instance.

	    Usage example:
	      >>> usage = """ COMMAND ARGUMENTS...
	      ...
	      ...             Command description.
	      ...         """
	      >>> OptionParser(usage=format_usage(usage))

	    @param usage: the usage string.
	    @returns: the formatted string.
	'''
	def prefix_length(line):
		length = 0
		while length < len(line) and line[length] in (' ', '\t'):
			length += 1
		return length

	lines = usage.split('\n')
	while len(lines) and len(lines[0].strip()) == 0:
		del lines[0]
	while len(lines) and len(lines[-1].strip()) == 0:
		del lines[-1]

	plen = min(prefix_length(l) for l in lines if len(l.strip()) > 0)
	return '\n'.join(l[plen:] for l in lines)

def ArgumentParser(*args, **kwargs):
	''' A wrapper for the I{ArgumentParser} constructor which preserves
	    the formatting of the I{description}.
	'''
	if 'description' in kwargs:
		kwargs['formatter_class'] = argparse.RawDescriptionHelpFormatter
		kwargs['description'] = format_usage(kwargs['description'])
	return argparse.ArgumentParser(*args, **kwargs)

class safe_import (object):
	''' A block used to wrap import statements to provide user-friendly error
	    messages in case the import fails.

	    Usage example:
	      >>> with safe_import('pyparsing'):
	      ...     from pyparsing import *

	    If the import fails, the following error message is printed and the process
	    is terminated::

	      Cannot import library pyparsing. You probably need to install it on your system.
	'''
	def __init__(self, library):
		self.library = library

	def __enter__(self):
		pass

	def __exit__(self, type, value, traceback):
		if type is not None:
			if type == ImportError:
				exit('Cannot import library %s. You probably need to install it on your system.' % self.library)

def ignore_broken_pipe(func):
	''' If a broken pipe error (EPIPE) occurs while running B{func}, exit cleanly. '''
	try:
		func()
	except IOError, e:
		if e.errno == errno.EPIPE:
			sys.exit(0)
		else:
			raise

def min_python_version(*at_least):
	''' Checks if the running Python interpreter has a sufficiently recent version.

	    Usage example:
	      >>> min_python_version(2, 5, 2)
	'''

	def format_version(v):
		return '.'.join(str(d) for d in v)

	found = sys.version_info[:3]
	for e, f in zip(at_least, found):
		if f < e:
			exit('You need to upgrade your Python interpreter (found %s, need %s).' % (format_version(found), format_version(at_least)))
		elif f > e:
			return

def memory_usage():
	''' Returns the memory usage in bytes of the current process
	    on supported platforms. Raises an OSError otherwise. '''
	try:
		with file('/proc/%d/statm' % os.getpid(), 'r') as fd:
		        content = fd.read()
	except IOError:
		raise OSError, 'unsupported OS'

	tokens = content.strip().split()
	if len(tokens) != 7:
		raise OSError, 'unsupported OS'
	else:
		return int(tokens[0]) * 1024
