import sys

# look for lines with shortest prefix of len 4
PREFIX_SIZE = 2

if len(sys.argv) != 2:
	print("expected input file as argument...")

input_file = sys.argv[1]
cur_prefix = '0000'
cur_possible_vals = set(range(255))

found_shortest_prefixes = []

with open(input_file) as f:
	for i, line in enumerate(f):
		# TODO base these on prefix size. don't hardcode
		line = line.split(',')[0]
		line = line.strip('\n')
		line = line[2:]

		prefix, val = line[0:4], line[4:6]

		if prefix != cur_prefix:
			cur_prefix = prefix
			print(cur_prefix)
			if len(cur_possible_vals) != 0:
				import pdb; pdb.set_trace()
				found_shortest_prefixes += list(cur_possible_vals)

			cur_possible_vals = set(range(255))

		if int(val, 16) in cur_possible_vals:
			cur_possible_vals.remove(int(val, 16))

import pdb; pdb.set_trace()
