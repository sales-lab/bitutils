#ifndef STRTOK_H
#define STRTOK_H

typedef struct
{
	char* string;
	char* separators;
	char terminator;
	int terminator_found;
} strtok_info_t;

int strtok_init(strtok_info_t* info, char* string, const char* separators, const char terminator);
void strtok_clean(strtok_info_t* info);
char* strtok_get(strtok_info_t* info);
int strtok_terminator_found(const strtok_info_t* info);

#endif //STRTOK_H
