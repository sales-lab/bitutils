#include "reader.h"
#include <stdlib.h>
#include <string.h>
#include "strtok.h"

static int set_spec_stat(Reader* reader, const char* spec, int* spec_len, char** tokenized_spec)
{
	*spec_len = strlen(spec);
	if (*spec_len == 0)
	{
		PyErr_SetString(PyExc_ValueError, "empty spec");
		return -1;
	}
	
	char* spec_copy = (char*)malloc(*spec_len+2);
	if (spec_copy == NULL)
	{
		PyErr_SetString(PyExc_MemoryError, "out of memory");
		goto cleanup;
	}

	memcpy(spec_copy, spec, *spec_len+1);
	spec_copy[*spec_len+1] = 0;
	*tokenized_spec = spec_copy;
	
	reader->field_num = 0;
	reader->max_col_idx = -1;
	reader->verbatim_num = 0;
	
	char* spec_ptr = spec_copy;
	char* token;
	char* strtok_state;
	while ((token = strtok_r(spec_ptr, ",", &strtok_state)) != NULL)
	{
		spec_ptr = NULL;
		int token_len = strlen(token);
		
		if (token_len < 1)
		{
			PyObject* error_message = PyString_FromFormat("invalid token %s", token);
			if (error_message != NULL)
				PyErr_SetObject(PyExc_ValueError, error_message);
			goto cleanup;
		}
		else if (token_len == 1 && token[0] == 'a')
		{
			reader->field_num++;
			reader->verbatim_num++;
		}
		else
		{
			char *endptr;
			const int col_idx = strtol(token, &endptr, 10);
			if (endptr == token)
			{
				PyObject* error_message = PyString_FromFormat("invalid token %s", token);
				if (error_message != NULL)
					PyErr_SetObject(PyExc_ValueError, error_message);
				goto cleanup;
			}
			else if (errno == ERANGE || col_idx < 0)
			{
				PyObject* error_message = PyString_FromFormat("invalid column index in %s", token);
				if (error_message != NULL)
					PyErr_SetObject(PyExc_ValueError, error_message);
				goto cleanup;
			}
			
			reader->field_num++;
			if (col_idx > reader->max_col_idx)
				reader->max_col_idx = col_idx;
		}
	}
	
	return 0;

cleanup:
	free(spec_copy);
	*tokenized_spec = NULL;
	return -1;
}

static int parse_spec(Reader* reader, const int spec_len, char* tokenized_spec)
{
	if (reader->max_col_idx >= 0)
	{
		int cell_num = reader->max_col_idx + 1;
		reader->col_field_map = (ColumnSpec*)malloc(sizeof(ColumnSpec) * cell_num);
		if (reader->col_field_map == NULL)
		{
			PyErr_SetString(PyExc_MemoryError, "out of memory");
			goto cleanup;
		}
		
		while (cell_num > 0)
		{
			cell_num--;
			reader->col_field_map[cell_num].idx = -1;
		}
	}
	
	if (reader->verbatim_num > 0)
	{
		reader->verbatim_field_idxs = (int*)malloc(sizeof(int) * reader->verbatim_num);
		if (reader->verbatim_field_idxs == NULL)
		{
			PyErr_SetString(PyExc_MemoryError, "out of memory");
			goto cleanup;
		}
		
		reader->verbatim_num = 0;
	}
	
	int field_idx = 0;
	do
	{
		const int token_len = strlen(tokenized_spec);
		if (token_len == 1)
		{
			reader->verbatim_field_idxs[reader->verbatim_num] = field_idx;
			reader->verbatim_num++;
		}
		else
		{
			char* endptr;
			const int col_idx = strtol(tokenized_spec, &endptr, 10);
			if (endptr[1] != 0 || (endptr[0] != 's' && endptr[0] != 'u' && endptr[0] != 'i' && endptr[0] != 'f'))
			{
				PyObject* error_message = PyString_FromFormat("invalid column type in %s", tokenized_spec);
				if (error_message != NULL)
					PyErr_SetObject(PyExc_ValueError, error_message);
				goto cleanup;
			}
			
			reader->col_field_map[col_idx].idx = field_idx;
			reader->col_field_map[col_idx].type = *endptr;
		}
		
		tokenized_spec += token_len + 1;
		field_idx++;
	} while (*tokenized_spec != 0);
	
	return 0;

cleanup:
	if (reader->col_field_map != NULL)
		free(reader->col_field_map);
	if (reader->verbatim_field_idxs != NULL)
		free(reader->verbatim_field_idxs);
	return -1;
}

Reader* new_Reader(FILE *fd, const char* spec, const int allow_missing_cols)
{
	Reader* r = (Reader*)malloc(sizeof(Reader));
	if (r == NULL)
	{
		PyErr_SetString(PyExc_MemoryError, "out of memory");
		return NULL;
	}
	
	r->fd = fd;
	r->lineno = 0;
	r->allow_missing_cols = allow_missing_cols;
	r->col_field_map = NULL;
	r->verbatim_field_idxs = NULL;
	
	int spec_len;
	char* tokenized_spec = NULL;
	if (set_spec_stat(r, spec, &spec_len, &tokenized_spec) == -1 || parse_spec(r, spec_len, tokenized_spec) == -1)
	{
		if (tokenized_spec)
			free(tokenized_spec);
		free(r);
		r = NULL;
	}
	
	return r;
}

void delete_Reader(Reader* reader)
{
	if (reader->max_col_idx >= 0)
		free(reader->col_field_map);
	if (reader->verbatim_num > 0)
		free(reader->verbatim_field_idxs);
	free(reader);
}

PyObject* Reader_readline(Reader* reader)
{
	char line[65535], *fget_res;
	strtok_info_t sinfo;

	Py_BEGIN_ALLOW_THREADS
	fget_res = fgets(line, 65535, reader->fd);
	Py_END_ALLOW_THREADS

	if (fget_res == NULL)
	{
		if (ferror(reader->fd))
		{
			PyErr_SetString(PyExc_IOError, "cannot read line");
			return NULL;
		}
		else
		{
			Py_INCREF(Py_None);
			return Py_None;
		}
	}

	reader->lineno++;

	const int line_length = strlen(line);
	if (line_length == 0 || line[line_length-1] != '\n')
	{
		PyObject* error_message = PyString_FromFormat("unterminated string at line %lu (maybe the read buffer is too small?)", reader->lineno);
		if (error_message != NULL)
			PyErr_SetObject(PyExc_IOError, error_message);
		else
			PyErr_SetString(PyExc_MemoryError, "out of memory");
		return NULL;
	}

	if (!strtok_init(&sinfo, line, "\t", '\n'))
	{
		PyErr_SetString(PyExc_MemoryError, "out of memory");
		return NULL;
	}

	
	PyObject* tuple = PyTuple_New(reader->field_num);
	if (tuple == NULL)
	{
		PyErr_SetString(PyExc_MemoryError, "out of memory");
		return NULL;
	}
	
	if (reader->verbatim_num > 0)
	{
		PyObject* line_dup = PyString_FromString(line);
		if (line_dup == NULL)
		{
			PyErr_SetString(PyExc_MemoryError, "out of memory");
			goto cleanup;
		}
		
		int verbatim_idx = reader->verbatim_num;
		while (1)
		{
			verbatim_idx--;
			PyTuple_SetItem(tuple, reader->verbatim_field_idxs[verbatim_idx], line_dup);
			
			if (verbatim_idx == 0)
				break;
			else
				Py_INCREF(line_dup);
		}
	}
	
	int col_idx;
	if (reader->allow_missing_cols)
	{
		col_idx = reader->field_num;
		while (col_idx > 0)
		{
			Py_INCREF(Py_None);
			col_idx--;
			PyTuple_SetItem(tuple, col_idx, Py_None);
		}
	}
	else
		col_idx = 0;
	
	while (col_idx <= reader->max_col_idx)
	{
		char* token = strtok_get(&sinfo);
		if (token == NULL)
		{
			if (reader->allow_missing_cols)
				break;
			else
			{
				PyObject* error_message = PyString_FromFormat("insufficient token number at line %lu", reader->lineno);
				if (error_message != NULL)
					PyErr_SetObject(PyExc_IOError, error_message);
				else
					PyErr_SetString(PyExc_MemoryError, "out of memory");
				goto cleanup;
			}
		}
		
		const int field_idx = reader->col_field_map[col_idx].idx;
		if (field_idx != -1)
		{
			PyObject* value = NULL;
			char* endptr;
			switch (reader->col_field_map[col_idx].type)
			{
			case 's':
				value = PyString_FromString(token);
				if (value == NULL)
				{
					PyErr_SetString(PyExc_MemoryError, "out of memory");
					goto cleanup;
				}
				break;
			
			case 'u':
				value = PyLong_FromString(token, &endptr, 10);
				if (value == NULL || *endptr != 0 || PyLong_AsLong(value) < 0)
				{
					PyObject* error_message = PyString_FromFormat("invalid unsigned long at line %lu, column %d", reader->lineno, col_idx+1);
					if (error_message != NULL)
						PyErr_SetObject(PyExc_IOError, error_message);
					else
						PyErr_SetString(PyExc_MemoryError, "out of memory");
					goto cleanup;
				}
				break;
			
			case 'i':
				value = PyLong_FromString(token, &endptr, 10);
				if (value == NULL || *endptr != 0)
				{
					PyObject* error_message = PyString_FromFormat("invalid long at line %lu, column %d", reader->lineno, col_idx+1);
					if (error_message != NULL)
						PyErr_SetObject(PyExc_IOError, error_message);
					else
						PyErr_SetString(PyExc_MemoryError, "out of memory");
					goto cleanup;
				}
				break;
			
			case 'f':
				{
					PyObject* aux = PyString_FromString(token);
					if (aux == NULL)
					{
						PyErr_SetString(PyExc_MemoryError, "out of memory");
						goto cleanup;
					}
					
					value = PyFloat_FromString(aux, NULL);
					Py_DECREF(aux);
					if (value == NULL)
					{
						PyObject* error_message = PyString_FromFormat("invalid float at line %lu, column %d", reader->lineno, col_idx+1);
						if (error_message != NULL)
							PyErr_SetObject(PyExc_IOError, error_message);
						else
							PyErr_SetString(PyExc_MemoryError, "out of memory");
						goto cleanup;
					}
				}
				break;
			
			default:
				PyErr_SetString(PyExc_RuntimeError, "unexpected internal error");
				goto cleanup;
			}
			
			PyTuple_SetItem(tuple, field_idx, value);
		}
		
		col_idx++;
	}
	
	strtok_clean(&sinfo);
	return tuple;

cleanup:
	strtok_clean(&sinfo);
	Py_DECREF(tuple);
	return NULL;
}

unsigned long Reader_lineno(Reader* reader)
{
	return reader->lineno;
}
