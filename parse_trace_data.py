import sys, json, re, heapq

# return a map of contract_address: (copy count, gas spent), include reverted calls
# TODO figure out how to make the tracer emit gas spent in each call frame (without including internal calls)
def parse_contract_copies(tx_trace):
	result = {}
	if not 'gasUsed' in tx_trace:
		return None

	result[tx_trace['to']] = { 'consecutive_copies': [0], 'copy_count': len(tx_trace['copies']), 'gas_used': int(tx_trace['gasUsed'], 16), 'gas_used_mcopy': int(tx_trace['gasUsed'], 16)}

	if len(tx_trace['copies']) > 0:
		copies = measure_consecutive_copies(tx_trace['copies'])
		result[tx_trace['to']]['consecutive_copies'] = copies
		result[tx_trace['to']]['gas_used_mcopy'] = estimate_mcopy_savings(result[tx_trace['to']]['gas_used'], copies)

	for call in tx_trace['calls']:
		if not 'gasUsed' in call and call['output'] == '0x':
			# call to EOA/non-contract
			continue

		if call['to'] in result:
			result[call['to']]['copy_count'] += len(call['memcopyState']['copies'])
			result[call['to']]['gas_used'] += int(call['gasUsed'], 16)
			result[call['to']]['gas_used_mcopy'] += int(call['gasUsed'], 16)
		else:
			result[call['to']] = {'copy_count': len(call['memcopyState']['copies']), 'gas_used': int(call['gasUsed'], 16), 'gas_used_mcopy': int(call['gasUsed'], 16), 'consecutive_copies': [0]}

		if len(call['memcopyState']['copies']) > 0:
			consecutive_copies = measure_consecutive_copies(call['memcopyState']['copies'])
			result[call['to']]['consecutive_copies'] = consecutive_copies
			result[call['to']]['gas_used_mcopy'] = estimate_mcopy_savings(result[call['to']]['gas_used'], consecutive_copies)

		result[call['from']]['gas_used'] -= int(call['gasUsed'], 16)
		result[call['from']]['gas_used_mcopy'] -= int(call['gasUsed'], 16)

		assert result[call['from']]['gas_used'] >= 0, "whoops"
		assert result[call['from']]['gas_used_mcopy'] <= result[call['from']]['gas_used_mcopy'], "whoops"

	return result

def bulk_copy_bounds_check(start_src, start_dst, consec_count, next_src, next_dst):
	if next_src == start_src + consec_count * 32 and next_dst == start_dst + consec_count * 32:
		if start_src < start_dst:
			if start_src + consec_count * 32 >= start_dst:
				return False
			else:
				return True
		else:
			if start_dst + consec_count * 32 >= start_src:
				return False
			else:
				return True
	else:
		return False

def measure_consecutive_copies(call_copies):
	# quick-n-diry: just track ascending offsets in (start_offset, start_offset + 32, start_offset + 64, ...)
	cur_start = int(call_copies[0]['srcOffset'], 16)
	cur_dst = int(call_copies[0]['dstOffset'], 16)
	consecutive_counts = []
	cur_consecutive = 1

	for copy in call_copies[1:]:
		if bulk_copy_bounds_check(cur_start, cur_dst, cur_consecutive, int(copy['srcOffset'], 16), int(copy['dstOffset'], 16)):
			cur_consecutive += 1
		else:
			consecutive_counts.append(cur_consecutive)
			cur_consecutive = 1
			cur_start = int(copy['srcOffset'], 16)
			cur_dst = int(copy['dstOffset'], 16)

	consecutive_counts.append(cur_consecutive)
	return consecutive_counts 

# cost for mcopy from EIP (assuming no memory expansion)
def mcopy_cost_model(num_words):
	return 15 + 3 * num_words 

def estimate_mcopy_savings(non_mcopy_gas, copies) -> int:
	COST_PUSH = 3
	COST_MLOAD = 3
	COST_MSTORE = 3

	result = non_mcopy_gas

	for copy_size in copies:
		result -= (COST_PUSH + COST_MLOAD + COST_PUSH + COST_PUSH + COST_MSTORE) * copy_size
		result += COST_PUSH + COST_PUSH + mcopy_cost_model(copy_size)

	return result

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
			print(tx)

			if i + 1 >= len(trace_lines):
				break
			elif trace_lines[i + 1] == 'error':
				i += 1
			elif trace_lines[i + 1].startswith("{"):
				trace_result = json.loads(trace_lines[i + 1].replace("'", '"').replace('None', '"None"'))

				copies = parse_contract_copies(trace_result)

				for k, v in zip(copies.keys(), copies.values()):
					if k in max_copy_sizes:
						max_copy_sizes[k] = max(max_copy_sizes[k], max(v['consecutive_copies']))
					else:
						max_copy_sizes[k] = max(v['consecutive_copies'])

					if not k in aggregate_copies:
						aggregate_copies[k] = {'copy_count': 0, 'gas_used': 0, 'gas_used_mcopy': 0}

					aggregate_copies[k]['copy_count'] += v['copy_count']
					aggregate_copies[k]['gas_used'] += v['gas_used']
					import pdb; pdb.set_trace()
					aggregate_copies[k]['gas_used_mcopy'] += v['gas_used_mcopy']

				i += 1

		i += 1

	aggregate_copies = zip(aggregate_copies.keys(), aggregate_copies.values())
	aggregate_copies = list(reversed(sorted(aggregate_copies, key=lambda x: x[1]['copy_count'])))

	max_copy_sizes = zip(max_copy_sizes.keys(), max_copy_sizes.values())
	max_copy_sizes = list(reversed(sorted(max_copy_sizes, key=lambda x: x[1])))

	print("aggregate copy-count/gas-consumed graph csv:")
	print()
	print("contract,total-copy-count,total-gas-used,total-mcopy-gas-used")
	for c in aggregate_copies[:10]:
		print(c[0],c[1]['copy_count'],c[1]['gas_used']), c[1]['gas_used_mcopy']

	print()
	print()
	print("contracts with largest consecutive copy sizes csv:")
	print()
	print("contract,consec-copy-count")
	for c in max_copy_sizes[:10]:
		print(c[0],c[1])

if __name__ == "__main__":
	main()
