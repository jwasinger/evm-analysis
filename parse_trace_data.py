import sys, json, re, heapq

# return a map of contract_address: (copy count, gas spent), include reverted calls
# TODO figure out how to make the tracer emit gas spent in each call frame (without including internal calls)
def parse_contract_copies(tx_trace):
	result = {}
	if not 'gasUsed' in tx_trace:
		return None

	result[tx_trace['to']] = { 'max_consecutive_copies': 0, 'copy_count': len(tx_trace['copies']), 'gas_used': int(tx_trace['gasUsed'], 16)}

	if len(tx_trace['copies']) > 0:
		result[tx_trace['to']]['max_consecutive_copies'] = measure_consecutive_copies(tx_trace['copies'])

	for call in tx_trace['calls']:
		if not 'gasUsed' in call and call['output'] == '0x':
			# call to EOA/non-contract
			continue

		if call['to'] in result:
			result[call['to']]['copy_count'] += len(call['memcopyState']['copies'])
			result[call['to']]['gas_used'] += int(call['gasUsed'], 16)
		else:
			result[call['to']] = {'copy_count': len(call['memcopyState']['copies']), 'gas_used': int(call['gasUsed'], 16), 'max_consecutive_copies': 0}

		if len(call['memcopyState']['copies']) > 0:
			result[call['to']]['max_consecutive_copies'] = measure_consecutive_copies(call['memcopyState']['copies'])

		result[call['from']]['gas_used'] -= int(call['gasUsed'], 16)
		assert result[call['from']]['gas_used'] >= 0, "whoops"

	return result

def measure_consecutive_copies(call_copies):
	# quick-n-diry: just track ascending offsets in (start_offset, start_offset + 32, start_offset + 64, ...)
	cur_start = int(call_copies[0]['srcOffset'], 16)
	cur_dst = int(call_copies[0]['dstOffset'], 16)
	cur_consecutive = 1
	max_consecutive = 1

	for copy in call_copies[1:]:
		if int(copy['srcOffset'], 16) == cur_start + cur_consecutive * 32 and int(copy['dstOffset'], 16) == cur_dst + cur_consecutive * 32: # TODO check that the src and dst blocks of memory do not overlap
			cur_consecutive += 1
		else:
			max_consecutive = max(cur_consecutive, max_consecutive)
			cur_consecutive = 1
			cur_start = int(copy['srcOffset'], 16)
			cur_dst = int(copy['dstOffset'], 16)

	max_consecutive = max(cur_consecutive, max_consecutive)

	return max_consecutive

def main():
	trace_file = sys.argv[1]
	trace_lines = None

	max_copy_sizes = {}
	aggregate_copies = {}

	with open(trace_file) as f:
		trace_lines = f.readlines()

	cur_tx = None
	cur_block = None

	i = 0
	tx = None
	while i < len(trace_lines):
		line = trace_lines[i]

		if line.startswith('tx: '):
			tx = line[4:]

			if i + 1 >= len(trace_lines):
				break
			elif trace_lines[i + 1] == 'error':
				i += 1
			elif trace_lines[i + 1].startswith("{"):
				print(tx)
				trace_result = json.loads(trace_lines[i + 1].replace("'", '"').replace('None', '"None"'))
				copies = parse_contract_copies(trace_result)
				for k, v in zip(copies.keys(), copies.values()):
					if k in max_copy_sizes:
						if v['max_consecutive_copies'] > max_copy_sizes[k]:
							max_copy_sizes[k] = v['max_consecutive_copies']
					else:
						max_copy_sizes[k] = v['max_consecutive_copies']

					if not k in aggregate_copies:
						aggregate_copies[k] = {'copy_count': 0, 'gas_used': 0}

					aggregate_copies[k]['copy_count'] += v['copy_count']
					aggregate_copies[k]['gas_used'] += v['gas_used']

				i += 1

		i += 1

	aggregate_copies = zip(aggregate_copies.keys(), copies.values())
	aggregate_copies = list(reversed(sorted(aggregate_copies, key=lambda x: x[1]['copy_count'])))

	max_copy_sizes = zip(max_copy_sizes.keys(), max_copy_sizes.values())
	max_copy_sizes = list(reversed(sorted(max_copy_sizes, key=lambda x: x[1])))

	import pdb; pdb.set_trace()

if __name__ == "__main__":
	main()
