cdef extern from "Python.h":
  ctypedef struct FILE
  FILE* PyFile_AsFile(object)


cdef extern from "reader.h":
  ctypedef struct Reader:
    pass

  Reader* new_Reader(FILE* fd, char* spec, int allow_missing_cols)
  void delete_Reader(Reader* reader)
  object Reader_readline(Reader* reader)
  unsigned long Reader_lineno(Reader* reader)
