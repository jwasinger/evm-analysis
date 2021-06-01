import sys, json, re, heapq

# contract call test case:

# 0x7a250d5630b4cf539739df2c5dacb4c659f2488d -> 0x2b6a25f7c54f43c71c743e627f5663232586c39f
# 0x7a250d5630b4cf539739df2c5dacb4c659f2488d -> 0x8a9c67fee641579deba04928c4bc45f66e26343a
# 0x7a250d5630b4cf539739df2c5dacb4c659f2488d -> 0x2b6a25f7c54f43c71c743e627f5663232586c39f
# 0x7a250d5630b4cf539739df2c5dacb4c659f2488d -> 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
# 0x7a250d5630b4cf539739df2c5dacb4c659f2488d -> 0x0fc0e5deb2208928d79fe38fbfa897a83a44e692

tx_test_case1 = {'type': 'CALL', 'from': '0x0fc0e5deb2208928d79fe38fbfa897a83a44e692', 'to': '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', 'value': '0x0', 'gas': '0x25786', 'gasUsed': '0x21177', 'input': '0x18cbafe5000000000000000000000000000000000000000000000a127b66b4afe6d6fc030000000000000000000000000000000000000000000000011841ec30d0673c9e00000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000fc0e5deb2208928d79fe38fbfa897a83a44e692000000000000000000000000000000000000000000000000000000005f1df98f00000000000000000000000000000000000000000000000000000000000000020000000000000000000000008a9c67fee641579deba04928c4bc45f66e26343a000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'output': '0x00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000a127b66b4afe6d6fc030000000000000000000000000000000000000000000000011b0f61c0a986fd3a', 'time': '19.322094988s', 'calls': [{'type': 'STATICCALL', 'from': '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', 'to': '0x2b6a25f7c54f43c71c743e627f5663232586c39f', 'input': '0x0902f1ac', 'memcopyState': {'candidates': [], 'copies': [], 'prevOp': {'name': 'RETURN', 'pc': 788, 'stack': ['80', '60', '902f1ac']}}, 'gas': '0x24081', 'gasUsed': '0x4b4', 'output': '0x00000000000000000000000000000000000000000001e2dbf64db0807bdc4ffe00000000000000000000000000000000000000000000003645bdcbb017247663000000000000000000000000000000000000000000000000000000005f1df467'}, {'type': 'CALL', 'from': '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', 'to': '0x8a9c67fee641579deba04928c4bc45f66e26343a', 'input': '0x23b872dd0000000000000000000000000fc0e5deb2208928d79fe38fbfa897a83a44e6920000000000000000000000002b6a25f7c54f43c71c743e627f5663232586c39f000000000000000000000000000000000000000000000a127b66b4afe6d6fc03', 'memcopyState': {'candidates': [], 'copies': [], 'prevOp': {'name': 'RETURN', 'pc': 1695, 'stack': ['0', '20', '1', '1', '82582c4271f3f6dd5f4306cbcac822076516c53', '211', '75', '23b872dd']}}, 'value': '0x0', 'gas': '0x22ec6', 'calls': [{'type': 'DELEGATECALL', 'from': '0x8a9c67fee641579deba04928c4bc45f66e26343a', 'to': '0x082582c4271f3f6dd5f4306cbcac822076516c53', 'input': '0x23b872dd0000000000000000000000000fc0e5deb2208928d79fe38fbfa897a83a44e6920000000000000000000000002b6a25f7c54f43c71c743e627f5663232586c39f000000000000000000000000000000000000000000000a127b66b4afe6d6fc03', 'memcopyState': {'candidates': [], 'copies': [{'srcOffset': '0', 'srcPC': 2714, 'dstOffset': '80', 'dstPC': 2725}], 'prevOp': {'name': 'RETURN', 'pc': 555, 'stack': ['80', '20', '23b872dd']}}, 'gas': '0x21b77', 'gasUsed': '0x60d1', 'output': '0x'}], 'gasUsed': '0x6bbc', 'output': '0x'}, {'type': 'CALL', 'from': '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', 'to': '0x2b6a25f7c54f43c71c743e627f5663232586c39f', 'input': '0x022c0d9f00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011b0f61c0a986fd3a0000000000000000000000007a250d5630b4cf539739df2c5dacb4c659f2488d00000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000', 'memcopyState': {'candidates': [], 'copies': [{'srcOffset': 'e0', 'srcPC': 8366, 'dstOffset': '124', 'dstPC': 8368}, {'srcOffset': '100', 'srcPC': 8366, 'dstOffset': '144', 'dstPC': 8368}], 'prevOp': {'name': 'STOP', 'pc': 600, 'stack': ['22c0d9f']}}, 'value': '0x0', 'gas': '0x1b78a', 'calls': [{'type': 'CALL', 'from': '0x2b6a25f7c54f43c71c743e627f5663232586c39f', 'to': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'input': '0xa9059cbb0000000000000000000000007a250d5630b4cf539739df2c5dacb4c659f2488d0000000000000000000000000000000000000000000000011b0f61c0a986fd3a', 'memcopyState': {'candidates': [], 'copies': [], 'prevOp': {'name': 'RETURN', 'pc': 969, 'stack': ['60', '20', 'a9059cbb']}}, 'value': '0x0', 'gas': '0x188a9', 'gasUsed': '0x75d2', 'output': '0x'}, {'type': 'STATICCALL', 'from': '0x2b6a25f7c54f43c71c743e627f5663232586c39f', 'to': '0x8a9c67fee641579deba04928c4bc45f66e26343a', 'input': '0x70a082310000000000000000000000002b6a25f7c54f43c71c743e627f5663232586c39f', 'memcopyState': {'candidates': [], 'copies': [], 'prevOp': {'name': 'RETURN', 'pc': 1695, 'stack': ['0', '20', '1', '1', '82582c4271f3f6dd5f4306cbcac822076516c53', '211', '75', '70a08231']}}, 'gas': '0x10db8', 'calls': [{'type': 'DELEGATECALL', 'from': '0x8a9c67fee641579deba04928c4bc45f66e26343a', 'to': '0x082582c4271f3f6dd5f4306cbcac822076516c53', 'input': '0x70a082310000000000000000000000002b6a25f7c54f43c71c743e627f5663232586c39f', 'memcopyState': {'candidates': [], 'copies': [], 'prevOp': {'name': 'RETURN', 'pc': 581, 'stack': ['80', '20', '70a08231']}}, 'gas': '0xfef6', 'gasUsed': '0x51a', 'output': '0x'}], 'gasUsed': '0xffc', 'output': '0x00000000000000000000000000000000000000000001ecee71b4653062b34c01'}, {'type': 'STATICCALL', 'from': '0x2b6a25f7c54f43c71c743e627f5663232586c39f', 'to': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'input': '0x70a082310000000000000000000000002b6a25f7c54f43c71c743e627f5663232586c39f', 'memcopyState': {'candidates': [], 'copies': [], 'prevOp': {'name': 'RETURN', 'pc': 737, 'stack': ['60', '20', '2cc', '70a08231']}}, 'gas': '0xf7c9', 'gasUsed': '0x4d2', 'output': '0x0000000000000000000000000000000000000000000000352aae69ef6d9d7929'}], 'gasUsed': '0x1230f', 'output': '0x'}, {'type': 'CALL', 'from': '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', 'to': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'input': '0x2e1a7d4d0000000000000000000000000000000000000000000000011b0f61c0a986fd3a', 'memcopyState': {'candidates': [], 'copies': [], 'prevOp': {'name': 'STOP', 'pc': 613, 'stack': ['2e1a7d4d']}}, 'value': '0x0', 'gas': '0x926f', 'calls': [{'type': 'CALL', 'from': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'to': '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', 'input': '0x', 'memcopyState': {'candidates': [], 'copies': [], 'prevOp': {'name': 'STOP', 'pc': 468, 'stack': []}}, 'value': '0x11b0f61c0a986fd3a', 'gas': '0x8fc', 'gasUsed': '0x53', 'output': '0x'}], 'gasUsed': '0x2e93', 'output': '0x'}, {'type': 'CALL', 'from': '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', 'to': '0x0fc0e5deb2208928d79fe38fbfa897a83a44e692', 'input': '0x', 'memcopyState': {'candidates': [], 'copies': [], 'prevOp': 'None'}, 'value': '0x11b0f61c0a986fd3a', 'output': '0x'}], 'copies': [{'srcOffset': '2da', 'srcPC': 16988, 'dstOffset': '33e', 'dstPC': 16990}, {'srcOffset': '2fa', 'srcPC': 16988, 'dstOffset': '35e', 'dstPC': 16990}, {'srcOffset': '31a', 'srcPC': 16988, 'dstOffset': '37e', 'dstPC': 16990}, {'srcOffset': '49b', 'srcPC': 17756, 'dstOffset': '49b', 'dstPC': 17758}, {'srcOffset': 'e0', 'srcPC': 843, 'dstOffset': '4db', 'dstPC': 847}, {'srcOffset': '100', 'srcPC': 880, 'dstOffset': '100', 'dstPC': 884}, {'srcOffset': '120', 'srcPC': 880, 'dstOffset': '100', 'dstPC': 884}]}

def print_tx_trace_calls(tx_trace):
	for call in tx_trace['calls']:
		print("{} -> {}".format(call['from'], call['to']))

def parse_tx_2(tx_trace):
	call_graph = [{'address': tx_trace['to'], 'calls': []}]
	call_stack = [{'address': tx_trace['to'], 'call_graph_node': call_graph[0]}]
	cur_node = call_graph[0]

	for call in tx_trace['calls']:
		import pdb; pdb.set_trace()
		if call['from'] == call_stack[-1]['address']:
			# call is recursing into a new frame
			new_node = {'address': call['to'], 'calls': []}
			cur_node['calls'].append(new_node)
			cur_node = new_node
			call_stack.append({'address': call['to'], 'call_graph_node': cur_node})
		else:
			# previous call frame(s) ended, call is from some parent frame
			call_stack.pop(-1)
			while len(call_stack) > 0:
				if call_stack[-1]['address'] == call['from']:
					call_stack[-1]['call_graph_node']['calls'].append({
						'address': call['to'],
						'calls': [],
					})
					cur_node = call_stack[-1]['call_graph_node']
					break
				else:
					call_stack.pop(-1)

	return call_graph

result1 = parse_tx_2(tx_test_case1)
import pdb; pdb.set_trace()

# return a map of contract_address: (copy count, gas spent), include reverted calls
# TODO figure out how to make the tracer emit gas spent in each call frame (without including internal calls)
def parse_contract_copies(tx_trace):
	result = {}
	if not 'gasUsed' in tx_trace:
		return None

	result = parse_tx(tx_trace)
	import pdb; pdb.set_trace()
	return

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

				copies = parse_tx(trace_result)
				import pdb; pdb.set_trace()

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
