#include "Python.h"

typedef struct
{
	int idx;
	char type;
} ColumnSpec;

typedef struct
{
	FILE* fd;
	unsigned long lineno;
	int allow_missing_cols;
	int field_num;
	int max_col_idx;
	ColumnSpec* col_field_map;
	int verbatim_num;
	int* verbatim_field_idxs;
} Reader;

Reader* new_Reader(FILE* fd, const char* spec, const int allow_missing_cols);
void delete_Reader(Reader* reader);
PyObject* Reader_readline(Reader* reader);
unsigned long Reader_lineno(Reader* reader);
