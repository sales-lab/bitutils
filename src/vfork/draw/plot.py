''' Standard plots. '''

from .coords import Transformer
from math import pi

class CGVPlot(object):
	def __init__(self, original_x, original_y, original_w, original_h, surface):
		self.surface = surface
		self.surface.line_width = 3
		self.surface.set_round_caps()
		self.transformer = Transformer(original_x, original_y, original_w, original_h, self.surface.width, self.surface.height)
	
	def draw_horizontal_region(self, y, h, rgba):
		y, h = self.transformer.transform_vertical_region(y, h)
		if y is not None:
			self.surface.rgba = rgba
			self.surface.fill_rectangle(0, self.surface.height-y-h, self.surface.width, h)

	def draw_vertical_region(self, x, w, rgba):
		x, w = self.transformer.transform_horizontal_region(x, w)
		if x is not None:
			self.surface.rgba = rgba
			self.surface.fill_rectangle(x, 0, w, self.surface.height)
	
	def draw_segment(self, x1, x2, y1, y2, rgba):
		x1, y1, x2, y2 = self.transformer.transform_segment(x1, y1, x2, y2)
		if x1 is None:
			return	

		self.surface.rgba = rgba
		line_width = self.surface.line_width
		if abs(x2-x1) < line_width and abs(y2-y1) < line_width:
			self.surface.fill_arc(x1, self.surface.height-y1, self.surface.line_width/2, 0, 2*pi)
		else:
			self.surface.draw_line(x1, self.surface.height-y1, x2, self.surface.height-y2)
