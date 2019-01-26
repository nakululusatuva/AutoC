import AutoC
m = AutoC.header('project', '/home/user/project/include/internal', '/home/user/project/include/outer')
m.add_paragraph_patterns([['// BEGIN\n', '// END\n']])
m.add_regex_patterns([r'^#\w+'])
m.add_leading_patterns(['/', '*'])
m.add_contained_patterns(['test'])
m.add_whole_patterns(['#include "common.h\n"'])
m.add_top_constants(['#ifndef XXX\n', '#define XXX\n'])
m.add_bottom_constants(['#endif\n'])
m.add_include_dependency({
		'moduleA': ['common'],
		'moduleB': ['common'],
		'moduleC': ['moduleA', 'moduleB']
})
m.add_quotes([['extern "C" {\n', '}\n']])
m.generate('012345678')