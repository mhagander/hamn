from html.parser import HTMLParser
import tidylib
import urllib.parse

def TruncateAndClean(txt):
	# First apply Tidy
	(txt, errors) = tidylib.tidy_document(txt,
										  options={
											  'drop_proprietary_attributes': 1,
											  'alt_text': '',
											  'hide_comments': 1,
											  'output_xhtml': 1,
											  'show_body_only': 1,
											  'clean': 1,
											  'char_encoding': 'utf8',
											  'show-warnings': 0,
											  'show-info': 0,
										  })

	if errors:
		raise Exception("Tidy failed: %s" % errors)

	# Then truncate as necessary
	ht = HtmlTruncator(2048)
	ht.feed(txt)
	out = ht.GetText()

	# Remove initial <br /> tags
	while out.startswith('<br'):
		out = out[out.find('>')+1:]

	return out

class HtmlTruncator(HTMLParser):
	def __init__(self, maxlen):
		HTMLParser.__init__(self)
		self.len = 0
		self.maxlen = maxlen
		self.fulltxt = ''
		self.trunctxt = ''
		self.tagstack = []
		self.skiprest = False
	
	def feed(self, txt):
		txt = txt.lstrip()
		self.fulltxt += txt
		HTMLParser.feed(self, txt)

	def handle_startendtag(self, tag, attrs):
		if self.skiprest: return
		self.trunctxt += self.get_starttag_text()
	
	def quoteurl(self, str):
		p = str.split(":",2)
		if len(p) < 2:
			# Don't crash on invalid URLs
			return ""
		return p[0] + ":" + urllib.parse.quote(p[1])

	def cleanhref(self, attrs):
		if attrs[0] == 'href':
			return 'href', self.quoteurl(attrs[1])
		return attrs

	def handle_starttag(self, tag, attrs):
		if self.skiprest: return
		self.trunctxt += "<" + tag
		self.trunctxt += (' '.join([(' %s="%s"' % (k,v)) for k,v in map(self.cleanhref, attrs)]))
		self.trunctxt += ">"
		self.tagstack.append(tag)

	def handle_endtag(self, tag):
		if self.skiprest: return
		self.trunctxt += "</" + tag + ">"
		self.tagstack.pop()

	def handle_entityref(self, ref):
		self.len += 1
		if self.skiprest: return
		self.trunctxt += "&" + ref + ";"

	def handle_data(self, data):
		self.len += len(data)
		if self.skiprest: return
		self.trunctxt += data
		if self.len > self.maxlen:
			# Passed max length, so truncate text as close to the limit as possible
			self.trunctxt = self.trunctxt[0:len(self.trunctxt)-(self.len-self.maxlen)]

			# Now append any tags that weren't properly closed
			self.tagstack.reverse()
			for tag in self.tagstack:
				self.trunctxt += "</" + tag + ">"
			self.skiprest = True

			# Finally, append the continuation chars
			self.trunctxt += "[...]"

	def GetText(self):
		if self.len > self.maxlen:
			return self.trunctxt
		else:
			return self.fulltxt
