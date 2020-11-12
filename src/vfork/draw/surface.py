''' Draw surfaces using the Cairo engine. '''

from cStringIO import StringIO
import cairo

class PNGSurface(object):
	def __init__(self, width, height):
		self.width = int(width)
		self.height = int(height)
		self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
		self.ctx = cairo.Context(self.surface)
	
	def set_round_caps(self):
		self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	
	def draw_line(self, x1, y1, x2, y2):
		self.ctx.move_to(x1, y1)
		self.ctx.line_to(x2, y2)
		self.ctx.close_path()
		self.ctx.stroke()
	
	def draw_text(self, x, y, text):
		self.ctx.move_to(x, y)
		self.ctx.show_text(text)
	
	def fill_arc(self, x, y, radius, angle1, angle2):
		self.ctx.arc(x, y, radius, angle1, angle2)
		self.ctx.fill()
	
	def fill_rectangle(self, x, y, w, h):
		self.ctx.rectangle(x, y, w, h)
		self.ctx.fill()
	
	def fill_polygon(self, points):
		self.ctx.move_to(*points[0])
		for pnt in points[1:]:
			self.ctx.line_to(*pnt)
		self.ctx.close_path()
		self.ctx.fill()
	
	def write_to_file(self, file):
		self.surface.write_to_png(file)
	
	def write_to_buffer(self):
		buffer = StringIO()
		self.surface.write_to_png(buffer)
		return buffer.getvalue()
	
	def _get_line_width(self):
		return self.ctx.get_line_width()

	def _set_line_width(self, width):
		self.ctx.set_line_width(width)
	
	def _get_rgba(self):
		return self.ctx.get_source_rgba()
	
	def _set_rgba(self, rgba):
		self.ctx.set_source_rgba(*rgba)
	
	def _set_font_size(self, size):
		self.ctx.set_font_size(size)
	
	line_width = property(_get_line_width, _set_line_width)
	rgba = property(_get_rgba, _set_rgba)
	font_size = property(None, _set_font_size)

