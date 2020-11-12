''' Transformations between coordinate systems and clipping. '''

from __future__ import division

class Transformer(object):
	''' This class performs coordinate translation, scaling and clipping. '''
	
	TOP    = 1
	BOTTOM = 2
	RIGHT  = 4
	LEFT   = 8
	
	def __init__(self, original_x, original_y, original_w, original_h, space_w, space_h):
		''' Instantiates a transformer, setting the coordinates of the original
		    space and the dimensions of the target one.
		
		    It is assumed that the origin of the target space is (0, 0).
		
		    @param original_x: the origin x coordinate of the original space.
		    @param original_y: the origin y coordinate of the original space.
		    @param original_w: the width of the original space.
		    @param original_h: the height of the original space.
		    @param space_w: the width of the target space.
		    @param space_h: the height of the target space.
		'''
		assert original_w > 0, 'invalid width of the original space'
		assert original_h > 0, 'invalid height of the original space'
		assert space_w > 0, 'invalid width of the target space'
		assert space_h > 0, 'invalid height of the target space'
		
		self.original_x = original_x
		self.original_w = original_w
		self.original_y = original_y
		self.original_h = original_h
		
		self.space_w = space_w
		self.space_h = space_h
		
		self.scale_w = self.space_w / self.original_w
		self.scale_h = self.space_h / self.original_h
	
	def transform_horizontal_region(self, x, w):
		''' Transforms an horizontal region from the original to the target
		    space.
		
		    @param x: the start coordinate of the region.
		    @param w: the width of the region.
		    @returns: the transformed (x, w) coordinates or (None, None) if
		              the region is rejected.
		'''
		assert w > 0, 'invalid region width'
		
		if x + w < self.original_x or x > self.original_x + self.original_w:
			return None, None
		
		x = (x - self.original_x) * self.scale_w
		w = w * self.scale_w
		
		if x < 0:
			w += x
			x = 0
		if x + w > self.space_w:
			w = self.space_w - x
		
		return x, w
	
	def transform_vertical_region(self, y, h):
		''' Transforms a vertical region from the original to the target
		    space.
		
		    @param y: the start coordinate of the region.
		    @param h: the height of the region.
		    @returns: the transformed (y, h) coordinates or (None, None) if
		              the region is rejected.
		'''
		assert h > 0, 'invalid region width'
		
		if y + h < self.original_y or y > self.original_y + self.original_h:
			return None, None
		
		y = (y - self.original_y) * self.scale_h
		h = h * self.scale_h
		
		if y < 0:
			h += y
			y = 0
		if y + h > self.space_h:
			h = self.space_h - y
		
		return y, h
	
	def transform_segment(self, x1, y1, x2, y2):
		''' Transforms a segment from the original to the target space.
		
		    @param x1: the x coordinate of the starting point.
		    @param y1: the y coordinate of the stopping point.
		    @param x2: the x coordinate of the stopping point.
		    @param y2: the y coordinate of the stopping point.
		    @returns: the transformed (x1, y1, x2, y2) coordinates or
		              (None, None, None, None) if the segment is rejected.
		'''
		
		# translation & scaling
		w = (x2 - x1) * self.scale_w
		h = (y2 - y1) * self.scale_h
		
		x1 = (x1 - self.original_x) * self.scale_w
		x2 = x1 + w
		y1 = (y1 - self.original_y) * self.scale_h
		y2 = y1 + h
		
		# clipping (Cohen & Sutherland)
		region_code1 = self._comp_region_code(x1, y1)
		region_code2 = self._comp_region_code(x2, y2)
		
		while True:
			if not (region_code1 | region_code2):
				return x1, y1, x2, y2
			elif region_code1 & region_code2:
				return None, None, None, None
			else:
				outside_code = region_code1 if region_code1 != 0 else region_code2
				if outside_code & self.TOP:
					x = x1 + (x2 - x1) * (self.space_h - y1) / (y2 - y1)
					y = self.space_h
				elif outside_code & self.BOTTOM:
					x = x1 + (x2 - x1) * (-y1) / (y2 - y1)
					y = 0
				elif outside_code & self.RIGHT:
					y = y1 + (y2 - y1) * (self.space_w - x1) / (x2 - x1)
					x = self.space_w
				else:
					y = y1 + (y2 - y1) * (-x1) / (x2 - x1)
					x = 0
				
				if outside_code == region_code1:
					x1 = x
					y1 = y
					region_code1 = self._comp_region_code(x1, y1)
				else:
					x2 = x
					y2 = y
					region_code2 = self._comp_region_code(x2, y2)
	
	def _comp_region_code(self, x, y):
		''' Computes I{Cohen & Sutherland} region code for one point.
		
		    @param x: the x coordinate of the point.
		    @param y: the y coordinate of the point.
		    @returns: the region code.
		'''
		code = 0
		
		if y > self.space_h:
			code |= self.TOP
		elif y < 0:
			code |= self.BOTTOM
		
		if x > self.space_w:
			code |= self.RIGHT
		elif x < 0:
			code |= self.LEFT
		
		return code
