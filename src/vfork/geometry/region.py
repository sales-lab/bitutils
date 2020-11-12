from math import ceil, log

def region_overlap(region, start, stop):
	''' Checks if two regions overlap.
	
	    @param region: the (start, stop) coordinates of the first region.
	    @param start: the start coordinate of the second region.
	    @param stop: the stop coordinate of the second region.
	    @return: a boolean indicating if the two regions overlap.
	'''
	return not (region[0] >= stop or region[1] <= start)

class Index(object):
	''' An index for searching efficiently a list of bidimensional
	    regions.
	'''

	def __init__(self, regions, granularity=16):
		''' Builds the index.
		    
		    @param regions: a non-empty list of (start, stop, ...)
		                    tuples. Each tuple can contain an arbitrary
		                    number of fields as long as the first two
		                    represent the region coordinates.
		    @param granularity: the number of regions to keep in each
		                        leaf of the index.
		'''
		assert len(regions) > 0, 'region list is empty'
		self.regions = regions
		self.level_num, self.granularity, self.heap = self._build_heap(granularity)
		#self._check_heap()
	
	def get_overlapping(self, start, stop):
		''' Searches the index for regions overlapping the given span.

		    @param start: the start coordinate of the query span.
		    @param stop: the stop coordinate of the target span.
		    @return: a list of regions.
		'''
		horizon = []
		if self.heap[0] is not None and region_overlap(self.heap[0], start, stop):
			horizon.append(self.heap[0])
		if self.heap[1] is not None and region_overlap(self.heap[1], start, stop):
			horizon.append(self.heap[1])
		
		level = 2
		while len(horizon) and level < self.level_num:
			new_horizon = []
			for node in horizon:
				child = self.heap[node[2]]
				if child is not None and region_overlap(child, start, stop):
					new_horizon.append(child)
				
				child = self.heap[node[2]+1]
				if child is not None and region_overlap(child, start, stop):
					new_horizon.append(child)
			
			horizon = new_horizon
			level += 1
		
		res = []
		for node in horizon:
			j = node[2]
			j2 = j + self.granularity
			while j < len(self.regions) and j < j2:
				region = self.regions[j]
				if region_overlap(region, start, stop):
					res.append(region)
				j += 1
		
		return res
	
	def _build_heap(self, granularity):
		region_num = len(self.regions)
		block_num, level_num, granularity = self._compute_levels(region_num, granularity)
		heap_size = max(2, 2**level_num)
		heap = [None] * heap_size
		
		# fill the last level with region indexes
		i = 2**(level_num-1) - 2
		j = 0
		while j < region_num:
			start = self.regions[j][0]
			stop = self.regions[j][1]
			idx = j
			
			j2 = min(region_num, j+granularity)
			j += 1
			while j < j2:
				if stop < self.regions[j][1]:
					stop = self.regions[j][1]
				j += 1
			
			heap[i] = (start, stop, idx)
			i += 1
		
		# fill other levels with span informations
		level = level_num - 2
		while level > 0:
			base_idx = 2**level - 2
			children_base_idx = 2**(level+1) - 2
			
			i = base_idx
			j = children_base_idx
			while i < children_base_idx:
				if heap[j] is None:
					break
				elif heap[j+1] is None:
					heap[i] = (heap[j][0], heap[j][1], j)
				else:
					heap[i] = (heap[j][0], max(heap[j][1], heap[j+1][1]), j)
				i += 1
				j += 2
			
			level -= 1
		
		return level_num, granularity, heap
	
	def _compute_levels(self, record_num, granularity):
		block_num = record_num // granularity
		if record_num % granularity > 0:
			block_num += 1
		
		level_num = int(ceil(log(block_num, 2))) + 1
		block_num = 2**(level_num-1)
		granularity = int(ceil(record_num / block_num))
		
		return block_num, level_num, granularity
	
	# DEBUG
	def _check_heap(self):
		heap_size = len(self.heap)
		
		horizon = self.heap[:2]
		level = 2
		while level < self.level_num:
			new_horizon = []
			
			for node in horizon:
				child1 = self.heap[node[2]]
				if child1 is not None:
					assert node[0] == child1[0]
					new_horizon.append(child1)
				
				child2 = self.heap[node[2]+1]
				if child1 is None:
					assert child2 is None
				elif child2 is not None:
					assert node[1] == max(child1[1], child2[1])
					new_horizon.append(child2)
			
			level += 1
			horizon = new_horizon
		
		for idx, node in enumerate(horizon):
			j = node[2]
			if idx > 0:
				assert j - horizon[idx-1][2] == self.granularity
			
			start = self.regions[j][0]
			stop = self.regions[j][1]
			
			j2 = min(len(self.regions), j+self.granularity)
			j += 1
			while j < j2:
				if stop < self.regions[j][1]:
					stop = self.regions[j][1]
				j += 1
			
			assert node[0] == start
			assert node[1] == stop
