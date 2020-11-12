%module(docstring="Readers for tab-delimited files.") colreader
%{
#include "colreader.h"
%}

%include typemaps.i

%typemap(in) FILE * {
	if (!PyFile_Check($input))
	{
		PyErr_SetString(PyExc_TypeError, "need a file");
		return NULL;
	}
	$1 = PyFile_AsFile($input);
}

%exception Reader {
	$action
	if (result == NULL)
		return NULL;
}

%feature("docstring",
"This is an optimized reader for tab-delimited files.

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
") Reader;

%feature("docstring",
"Object constructor.

@param fd: a file object. Must be a real file descriptor.
@param spec: a description of the columns to be read.
@param allow_missing_cols: if B{False} the reader will raise an error when one of the input lines
       has too few columns to match the I{spec}.
") Reader(FILE*, const char*, const int);

%feature("docstring",
"Reads an input line, returning parsed values.

If I{allow_missing_cols} is B{True}, some values may be B{None}.

@returns: a tuple.
") readline;

%feature("docstring",
"Returns the line number of the last line read.

@returns: a line number.
") lineno;

typedef struct
{
	%extend {
		Reader(FILE *fd, const char* spec, const int allow_missing_cols);
		~Reader();
		PyObject* readline();
		unsigned long lineno();
		
		%pythoncode %{
			def __iter__(self):
				return self
			def next(self):
				tokens = self.readline()
				if tokens is None:
					raise StopIteration
				else:
					return tokens
		%}
	}
} Reader;
