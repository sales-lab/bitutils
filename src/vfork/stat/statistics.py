from math import log, floor, ceil, pow
from sys import stdin, stderr

class PvalueHisto(object):
	def __init__(self, min, max, n_bin):
		self.n_run = None
		self.min = log(min, 10)
		self.max = log(max, 10)
		self.n_bin = n_bin
		self.bin_size = float(self.max-self.min)/n_bin # the binning is a log binning
		self.histo = [0 for i in xrange(0, self.n_bin)]

	def write_in_file(self, fd, n_run):
		fd.seek(0)
		fd.truncate()
		fd.write(">%g\t%g\t%i\t%i\n" % (self.min, self.max, self.n_bin, n_run))
		for x,v in enumerate(self.histo):
			fd.write('%i\t%g\n' % (x, v))
		fd.flush()
	
		
	def value2bin_index(self, v, side="left"):
		v = log(v,10)
		#if v < self.min or v > self.max:
		#	raise ValueError("value out of range")
		if v < self.min:
			v = self.min
		if v > self.max:
			v = self.max
	
		x = (v - self.min) / self.bin_size
		if side == 'left':
			x = floor( x ); # approximation that make the p-value smaller (better)
		elif side == "right":
			x = ceil( x );  # approximation that make the p-value bigger (worst)

		if (side == 'right' or v == self.max) and x == self.n_bin:
			x-=1 # to allow get v \in [max-bin_size, max]
			
		return int(x)


	def put(self, v):
		x = self.value2bin_index(v, 'left') # the bins are left labelled: conservative approximation
		self.histo[x] += 1
	
	def get(self, v):
		x = self.value2bin_index(v, 'right') # we use get to test real p-values, then we make the pvalue bigger in the approximation
		return self.histo[x]
	
	def cumulate(self):
		self.cumulative = [0 for i in xrange(0, self.n_bin)]
		running_sum = 0
		for x, h in enumerate(self.histo):
			running_sum += h
			self.cumulative[x] = running_sum
	
	def get_smaller(self, v, normalize=False):
		x = self.value2bin_index(v, 'right') # we use get to test real p-values, then we make the pvalue bigger in the approximation
		try:
			if not normalize:
				return self.cumulative[x]
			else:
				return float(self.cumulative[x])/self.n_run
		except IndexError:
			print(v, x)
			raise NameError("self.cumulate is not defined. Call cumulate() methods before to call get_smaller()")
	
	def print_cumulative(self):
		#print self.max,  self.min + self.bin_size * self.n_bin
		print(pow(10, self.max))
		for x,v in enumerate(self.cumulative):
			print('%g\t%g' % (pow(10, self.min + self.bin_size * (x) ), v)) # the printied histogram has left labelled bins


class PvalueHistoFromFile(PvalueHisto):
	def __init__(self, fd):
		header = fd.readline()
		header.strip('>\n')
		tokens = header.split()
		assert len(tokens) == 4

		self.min, self.max, self.n_bin, self.n_run, self.histo = self.parse_hist_file(fd)

		self.bin_size = float(self.max-self.min)/self.n_bin # the binning is a log binning

	def parse_hist_file(self, fd):
		fd.seek(0)
		header = fd.next()
		tokens = header.strip('>\n').split()
		assert len(tokens) == 4
		min = float(tokens[0])
		max = float(tokens[1])
		n_bin = int(tokens[2])
		n_run = int(tokens[3])
		histo = [ 0 for i in xrange(0,n_bin)]
		for line in fd:
			line.rstrip()
			tokens = line.split()
			assert len(tokens)==2
			histo[int(tokens[0])] += int(tokens[1])
		return (min,max,n_bin,n_run,histo)
		
	def sum_form_file(self, fd, sum_n_run=True):
		min, max, n_bin, n_run, histo = self.parse_hist_file(fd)
		assert self.min == min
		assert self.max == max
		assert self.n_bin == n_bin

		if not sum_n_run: 
			if self.n_run != n_run:
				raise ValueError("if the n_run reported in the histo file are not summed then must be the same in each given histo file")
		else:
			self.n_run += n_run

		for i,v in enumerate(histo):
			self.histo[i] += v
