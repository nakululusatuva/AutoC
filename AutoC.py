import os
import re

class cmodule():
	name = ''
	location = ''
	headers = {}
	has_sub = False
	def __init__(self, name, location, headers, sub):
		self.name = name
		self.location = location
		self.headers = headers # name: location
		self.has_sub = sub

class header():
	# Basic infos
	project_name = str
	inner_dir = str
	outter_dir = str

	# Scanned modules
	modules = []

	# Deleting patterns
	leading_patterns = []
	contained_patterns = []
	paragraph_patterns = []
	whole_patterns = []
	regex_patterns = []

	# Include dependency between modules
	include_dependency = {}
	# Constant lines at the beginning/ending of the header file.
	top_constants = []
	bottom_constants = []
	# Quotes
	quotes = []

	def __init__(self, project_name, inner_dir, outer_dir):
		'''
		@param inner_dir: str (Relative direction of internal headers' folder)
		@param outter_dir: str (Relative dirsction of outter headers' folder)
		'''
		self.project_name = project_name
		self.inner_dir = inner_dir
		self.outter_dir = outer_dir
		self.scan()

	def scan(self):
		'''
		Scan the internal folder.
		'''
		i = 0
		root = ''
		for item in os.walk(self.inner_dir):
			# The first item is root dir.
			if i == 0:
				i+=1
				root = item[0]
				'''
				headers = {}
				for file in item[2]:
					headers[file] = item[0] + '/' + file
				self.modules.append(cmodule('', '', headers, True))
				'''
				for file in item[2]:
					headers = {}
					name = re.match(r"(\w+).h", file).group(1)
					headers[file] = item[0] + '/' + file
					self.modules.append(cmodule(name, '', headers, False))
				continue

			# Get module's infomations
			name = re.search(r"/(\w+)$", item[0]).group(1)
			location = re.search(root + r"/(.*?)$", item[0]).group(1).rstrip(name)
			headers = {}
			for file in item[2]:
				headers[file] = item[0] + '/' + file
			if len(item[1]) == 0:
				has_sub = False
			else:
				has_sub = True

			# Append to list
			self.modules.append(cmodule(name, location, headers, has_sub))
		self.print_scan_result()

	def print_scan_result(self):
		print("Detected module structure:")
		print("{:<4s}{:<12s}{:<24s}{}".format("No.", "Name", "Parents", "Headers"))
		print("-------------------------------------------------------")
		i = 0
		for m in self.modules:
			if m.name == '':
				for header_name, header_path in m.headers.items():
					print("{:<12s}{:<24s}{}".format('...', '...', header_name))
			else:
				parents = '...'
				headers = ''
				if len(m.location) != 0:
					parents = m.location
				if len(m.headers) != 0:
					for k, v in m.headers.items():
						headers += k + "  "
				else:
					headers = '...'
				print("{:<4s}{:<12s}{:<24s}{}".format(str(i), m.name, parents, headers))
				i += 1
		print("-------------------------------------------------------")

	def generate(self, mode_order):
		# Loop of modules
		for module in self.modules:
			# If the module represent the root of the internal headers folder.
			if module.name == '':
				for header_name, header_path in module.headers.items():
					header_lines = []
					with open(header_path, 'r') as f:
						header_lines = f.readlines()
					# Process the lines.
					header_lines = self.process(header_lines, module, mode_order)
					# Write to outter dir
					with open(self.outter_dir + '/' + header_name, 'w') as f:
						f.writelines(header_lines)
			else:
				headers_combination = []
				# Combine all the header files' lines into a list.
				for header_name, header_path in module.headers.items():
					with open(header_path, 'r') as f:
						headers_combination.extend(f.readlines())

				# Process the lines (remove/append).
				headers_combination = self.process(headers_combination, module, mode_order)

				# If the module don't have sub modules, create xx/xx/module.h directly.
				if module.has_sub == False and len(module.headers) != 0:
					direction = self.outter_dir + '/' + module.location
					if not os.path.exists(direction):
						os.makedirs(direction)
					with open(direction + module.name + ".h", 'w') as f:
						f.writelines(headers_combination)
				
				# If the module have sub modules, create xx/xx/module/module.h instead.
				elif module.has_sub == True and len(module.headers) != 0:
					direction = self.outter_dir + '/' + module.location + module.name + '/'
					if not os.path.exists(direction):
						os.makedirs(direction)
					with open(direction + module.name + ".h", 'w') as f:
						f.writelines(headers_combination)
		print("Done!")

	def process(self, lines, current_module, mode_order):
		print("Processing module: {}".format(current_module.name))
		new_lines = []
		new_lines.extend(lines)
		for c in mode_order:
			if c == '0':
				new_lines = self.process_paragraph_patterns(new_lines)
			elif c == '1':
				new_lines = self.process_regex_patterns(new_lines)
			elif c == '2':
				new_lines = self.process_leading_patterns(new_lines)
			elif c == '3':
				new_lines = self.process_contained_patterns(new_lines)
			elif c == '4':
				new_lines = self.process_whole_patterns(new_lines)
			elif c == '5':
				new_lines = self.process_top_constants(new_lines)
			elif c == '6':
				new_lines = self.process_bottom_constants(new_lines)
			elif c == '7':
				new_lines = self.process_include_dependency(new_lines, current_module)
			elif c == '8':
				new_lines = self.process_quotes(new_lines)
		new_lines = self.process_define(new_lines, current_module)
		return new_lines

	def add_paragraph_patterns(self, tokens):
		'''
		@param start_token: list (two-dimensional)
		The lines that between start_token and end_token will be removed, also the tokens.
		'''
		self.paragraph_patterns.extend(tokens)
	def process_paragraph_patterns(self, lines):
		if len(self.paragraph_patterns) == 0:
			return lines
		new_lines = []
		for tokens in self.paragraph_patterns: # paragraph pattern tags loop
			flag = True
			for l in lines: # lines loop
				if l == tokens[0]:
					flag = False
				elif l == tokens[1]:
					flag = True
					continue
				if flag:
					new_lines.append(l)
		return new_lines

	def add_regex_patterns(self, re):
		'''
		@param re: list (regex strings)
		The line that match the regex will be removed.
		'''
		self.regex_patterns.extend(re)
	def process_regex_patterns(self, lines):
		if len(self.regex_patterns) == 0:
			return lines
		new_lines = []
		for l in lines:
			i = 0
			for r in self.regex_patterns:
				if re.search(r, l, re.DOTALL) != None:
					break
				i+=1
			if i == len(self.regex_patterns):
				new_lines.append(l)
		return new_lines
				
	def add_leading_patterns(self, leading):
		'''
		@param leading: list
		The line that leading with the symbol in the parameter will be removed.
		'''
		self.leading_patterns.extend(leading)
	def process_leading_patterns(self, lines):
		if len(self.leading_patterns) == 0:
			return lines
		new_lines = []
		for l in lines:
			if l[0] in self.leading_patterns:
				continue
			else:
				new_lines.append(l)
		return new_lines

	def add_contained_patterns(self, contained):
		'''
		@param contained: list
		The line that contains the token in the parameter will be removed.
		'''
		self.contained_patterns.extend(contained)
	def process_contained_patterns(self, lines):
		if len(self.contained_patterns) == 0:
			return lines
		new_lines = []
		for l in lines:
			i = 0
			for p in self.contained_patterns:
				if p in l:
					break
				i += 1
			if i == len(self.contained_patterns):
				new_lines.append(l)
		return new_lines

	def add_whole_patterns(self, whole):
		'''
		@param whole: list
		The line that match the parameter will be removed.
		'''
		self.whole_patterns.extend(whole)
	def process_whole_patterns(self, lines):
		if len(self.whole_patterns) == 0:
			return lines
		new_lines = []
		for l in lines:
			i = 0
			for p in self.whole_patterns:
				if l == p:
					break
				i += 1
			if i == len(self.whole_patterns):
				new_lines.append(l)
		return new_lines

	def add_top_constants(self, constant_lines):
		'''
		@param constant_lines: list (Order: top->bottom)
		Add lines at the beginning of the header file.
		'''
		for l in constant_lines:
			if l[-1] != '\n':
				self.top_constants.append(l+'\n')
			else:
				self.top_constants.append(l)
	def process_top_constants(self, lines):
		if len(self.top_constants) == 0:
			return lines
		new_lines = []
		new_lines.extend(self.top_constants)
		new_lines.extend(lines)
		return new_lines

	def add_bottom_constants(self, constant_lines):
		'''
		@param constant_lines: list (Order: bottom->top)
		Add lines at the ending of the header file.
		'''
		for l in constant_lines:
			if l[-1] != '\n':
				self.bottom_constants.append(l+'\n')
			else:
				self.bottom_constants.append(l)
	def process_bottom_constants(self, lines):
		if len(self.bottom_constants) == 0:
			return lines
		new_lines = []
		new_lines.extend(lines)
		if new_lines[-1][-1] != '\n':
			new_lines[-1][-1] += '\n'
		new_lines.extend(self.bottom_constants)
		return new_lines

	def add_include_dependency(self, pairs):
		'''
		@param module: dict {'module': ['depend1', 'depend2', ...]}
		Add "#include <depend.h>" in "module.h"
		'''
		for pair in pairs.items():
			k_module = None
			v_module = []
			for m in self.modules:
				if m.name == pair[0]:
					k_module = m
				for depend in pair[1]:
					if m.name == depend:
						v_module.append(m)
			self.include_dependency[k_module] = v_module
	def process_include_dependency(self, lines, current_module):
		if len(self.include_dependency) == 0:
			return lines
		if current_module.name == '':
			return lines
		depends = []
		for k, v in self.include_dependency.items():
			if k.name == current_module.name:
				depends = v
				break
		path_prefix = ''
		depth = len(re.findall("/", current_module.location))
		for i in range(depth):
			path_prefix += '../'
		include_statements = []
		for d in depends:
			include_statements.append('#include "' + path_prefix + d.location + d.name + '.h"\n')
		include_statements.extend(lines)
		return include_statements

	def add_quotes(self, quotes):
		'''
		@param quotes: list (two-dimensional)
		Add paired lines at the top and at the bottom of the header.
		'''
		copy = []
		copy.extend(quotes)
		for quote in copy:
			if quote[0][-1] != '\n':
				quote[0] += '\n'
			if quote[1][-1] != '\n':
				quote[1] += '\n'
		self.quotes.extend(copy)
	def process_quotes(self, lines):
		if len(self.quotes) == 0:
			return lines
		new_lines = []
		new_lines.extend(lines)
		for quote in self.quotes:
			new_lines.insert(0, quote[0])
			if new_lines[-1][-1] != '\n':
				new_lines[-1][-1] += '\n'
			new_lines.append(quote[1])
		return new_lines

	def process_define(self, lines, current_module):
		new_lines = []
		name = '_' + self.project_name + '_' + current_module.name.upper() + '_H_'
		new_lines.append("#ifndef " + name + "\n")
		new_lines.append("#define " + name + "\n")
		new_lines.extend(lines)
		new_lines.append("#endif")
		return new_lines
