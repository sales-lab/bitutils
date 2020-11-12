cimport _colreader
cimport cpython


cdef class Reader:
  ''' This is an optimized reader for tab-delimited files.

It works by parsing just the columns the caller it's interested in,
with no unnecessary string copies (as opposed to the standard I{line.split()}
that has to produce a separate string for each token, no matter if it will
later be used or not).

The reader is built out of a I{spec} string describing the type of input the
caller wants to parse. For example::

  1u,3s

This I{spec} encodes for two fields; their description is separated by a comma,
with no intervening whitespace. The first field refers to the second column
(represented by the number 1, since all indexes are 0-based); it will be parsed as
an B{u}nsigned integer. The second field will be taken from the fourth column and
will be treated as a string (that means no conversion at all).

The available type codes are:
  - B{u}: unsigned integer
  - B{i}: integer
  - B{f}: float
  - B{s}: string (no conversion)
  - B{a}: the full line, including the trailing newline
'''

  cdef _colreader.Reader* __colreader

  def __cinit__(self, fd, spec, allow_missing=True):
    ''' Object constructor.

        @param fd: a file object. Must be a real file descriptor.
        @param spec: a description of the columns to be read.
        @param allow_missing_cols: if B{False} the reader will raise an error when
          one of the input lines has too few columns to match the I{spec}.
    '''
    cdef _colreader.FILE* naked = _colreader.PyFile_AsFile(fd)
    self.__colreader = _colreader.new_Reader(naked, spec, allow_missing)
    if self.__colreader is NULL:
      cpython.PyErr_NoMemory()

  def __dealloc__(self):
    if self.__colreader is not NULL:
      _colreader.delete_Reader(self.__colreader)

  def __iter__(self):
    return self

  def __next__(self):
    cdef object line = _colreader.Reader_readline(self.__colreader)
    if line is None:
      raise StopIteration
    else:
      return line

  def lineno(self):
    ''' Returns the line number of the last line read.

        @returns: a line number.
    '''
    return _colreader.Reader_lineno(self.__colreader)
