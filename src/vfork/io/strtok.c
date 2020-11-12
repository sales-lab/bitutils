#include "strtok.h"
#include <memory.h>
#include <stdlib.h>

int strtok_init(strtok_info_t* info, char* string, const char* separators, const char terminator)
{
	info->string = string;
	info->separators = strdup(separators);
	info->terminator = terminator;
	info->terminator_found = 0;

	return info->separators != NULL;
}

void strtok_clean(strtok_info_t* info)
{
	if (info->separators != NULL)
	{
		free(info->separators);
		info->separators = NULL;
	}
}

char* strtok_get(strtok_info_t* info)
{
	if (info->string == NULL)
		return NULL;
	
	char* s = info->string;
	char* c = s;
	while (1)
	{
		if (*c == 0 || *c == info->terminator)
		{
			info->string = NULL;
			if (*c == info->terminator)
			{
				info->terminator_found = 1;
				*c = 0;
			}
			return s;
		}
		else
		{
			const char* p = info->separators;
			while (*p != 0)
			{
				if (*c == *p)
				{
					info->string = c+1;
					*c = 0;
					return s;
				}
				else
					p++;
			}
			
			c++;
		}
	}
}

int strtok_terminator_found(const strtok_info_t* info)
{
	return info->terminator_found;
}

