from __future__ import with_statement

class SubstitutionMatrix(object):
	def __init__(self, filename):
		self.matrix = self._compute_degenerate_scores(self._load_matrix(filename))
		
	def __getitem__(self, key):
		return self.matrix[key]
	
	def _load_matrix(self, filename):
		rows = [ r.split(None) for r in self._load_rows(filename) ]
		
		if len(rows[0]) != 4:
			raise ValueError('invalid column header')
		for label in rows[0]:
			if label not in 'ACGT':
				raise ValueError('invalid column labels')
		
		matrix = {}
		for row in rows[1:]:
			if len(row) < 5:
				raise ValueError('too few columns')
			elif len(row) > 5:
				raise ValueError('too many columns')
			
			row_label = row[0]
			for column_label, score in zip(rows[0], row[1:]):
				try:
					matrix[row_label, column_label] = int(score)
				except ValueError:
					raise ValueError('invalid score')
		
		return matrix
	
	def _load_rows(self, filename):
		rows = []
		with file(filename, 'r') as fd:
			while len(rows) < 5:
				line = fd.readline()
				if len(line) == 0:
					raise ValueError('too few rows')
				elif line[0] == '#':
					continue
				else:
					rows.append(line.strip())
			
			while True:
				line = fd.readline()
				if len(line) == 0:
					break
				elif line[0] == '#':
					continue
				else:
					raise ValueError('too many rows')
		
		return rows
	
	def _compute_degenerate_scores(self, matrix):
		for x in 'ACGT':
			avg = sum(matrix[(x,y)] for y in 'ACGT') / 4
			matrix[(x,'N')] = int(round(avg))
		
		for y in 'ACGT':
			avg = sum(matrix[(x,y)] for x in 'ACGT') / 4
			matrix[('N',y)] = int(round(avg))
		
		avg = sum(matrix[(x,y)] for x in 'ACGT' for y in 'ACGT') / 16
		matrix[('N','N')] = int(round(avg))
		
		return matrix

