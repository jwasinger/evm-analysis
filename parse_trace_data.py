import sys, json, re, heapq

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
	return 3 + 3 * num_words

def estimate_mcopy_savings(non_mcopy_gas, copies) -> int:
	COST_PUSH = 3
	COST_MLOAD = 3
	COST_MSTORE = 3

	result = non_mcopy_gas

	for copy_size in copies:
		result -= (COST_PUSH + COST_MLOAD + COST_PUSH + COST_PUSH + COST_MSTORE) * copy_size
		result += COST_PUSH + COST_PUSH + mcopy_cost_model(copy_size)

	return result

# traverse the callgraph removing the cost of calling child contracts from parent gasUsed
# we need the aggregate gas spent in each contract (which doesn't include the cost of subcalls, other than cost of CALL itself)
# ---
# modifies tx_trace in-place
def trim_subcall_costs(tx_trace):
	if not 'gasUsed' in tx_trace:
		return 0

	if not 'calls' in tx_trace:
		# base case
		return int(tx_trace['gasUsed'], 16)
	else:
		call_gas_used = int(tx_trace['gasUsed'], 16)
		original_call_gas_used = call_gas_used

		for subcall in tx_trace['calls']:
			call_gas_used -= trim_subcall_costs(subcall)

		tx_trace['gasUsed'] = hex(call_gas_used)
		return call_gas_used

def aggregate_mcopy_savings(tx_trace):
	result = []

	# ignore calls to EOAs
	if not 'gasUsed' in tx_trace:
		return []

	# ignore copies executed in CREATE
	if not "to" in tx_trace:
		return []

	gas_used = int(tx_trace['gasUsed'], 16)
	gas_used_mcopy = gas_used
	
	consec_copies = []
	copies = []

	if "copies" in tx_trace:
		copies = tx_trace['copies']

	if len(copies) > 0:
		consec_copies = measure_consecutive_copies(copies)
		gas_used_mcopy = estimate_mcopy_savings(gas_used, consec_copies)
		assert gas_used_mcopy > 0, "shite"

	result += [{'account': tx_trace['to'], 'gas_used': gas_used, 'gas_used_mcopy': gas_used_mcopy, 'copies': copies, "consecutive_copies": consec_copies}]

	if 'calls' in tx_trace:
		for subcall in tx_trace['calls']:
			result += aggregate_mcopy_savings(subcall)

	return result

# return a map of contract_address: (copy count, gas spent), include reverted calls
# TODO figure out how to make the tracer emit gas spent in each call frame (without including internal calls)
def parse_contract_copies(tx_trace):
	trim_subcall_costs(tx_trace)

	# TODO sanity check which sums up call costs and makes sure that they sum up to the original "un-trimmed" trace

	savings = aggregate_mcopy_savings(tx_trace)
	return savings

def main():
	trace_file = sys.argv[1]
	trace_lines = None

	with open(trace_file) as f:
		trace_lines = f.readlines()

	cur_tx = None
	cur_block = None

	consecutive_copies = {}
	aggregate_savings = {}

	result = {}

	copy_size_occurances = {}
	total_gas_used = 0

	i = 0
	tx = None
	while i < len(trace_lines):
		line = trace_lines[i]

		if line.startswith('tx: '):
			tx = line[4:]
			# print(tx)

			if i + 1 >= len(trace_lines):
				break
			elif trace_lines[i + 1] == 'error':
				i += 1
			elif trace_lines[i + 1].startswith("{"):
				trace_result = json.loads(trace_lines[i + 1].replace("'", '"').replace('None', '"None"'))
				if 'gasUsed' in trace_result:
					total_gas_used += int(trace_result['gasUsed'], 16)

				copies = parse_contract_copies(trace_result)
				for acct in copies:
					consecutive_copies = acct['consecutive_copies']
					if len(consecutive_copies) == 0:
						consecutive_copies = [0]

					for copy_size in consecutive_copies:
						if copy_size == 0:
							continue

						if copy_size in copy_size_occurances:
							copy_size_occurances[copy_size] += 1
						else:
							copy_size_occurances[copy_size] = 1

					if len(consecutive_copies) > 0:
						# import pdb; pdb.set_trace()
						# continue
						pass

					if acct['account'] in result:
						entry = result[acct['account']]
						entry['gas_used'] += acct['gas_used']
						entry['gas_used_mcopy'] += acct['gas_used_mcopy']
						entry['max_consecutive_copies'] = max(entry['max_consecutive_copies'], max(consecutive_copies))
					else:
						result[acct['account']] = {
							'gas_used': acct['gas_used'],
							'gas_used_mcopy': acct['gas_used_mcopy'],
							'max_consecutive_copies': max(consecutive_copies)
						}
				i += 1

		i += 1

	max_consecutive = 0
	max_consecutive_acct = None

	for acct, value in result.items():
		if value['max_consecutive_copies'] > max_consecutive:
			max_consecutive_acct = acct
			max_consecutive = value['max_consecutive_copies']

	ENTRY_NUM=5

	# store data for graphs to csvs:

	with open('data/guzzlers.csv', 'w') as f:
		# pct savings for contracts with most gas usage
		max_savings = sorted(result.items(), key=lambda x: x[1]['gas_used'])

		f.write("account,\"aggregate percentage savings for most popular contracts with mcopy\"\n")
		for i in range(ENTRY_NUM):
			entry = max_savings[len(max_savings) - i - 1]
			pct_savings = ((entry[1]['gas_used'] - entry[1]['gas_used_mcopy']) / entry[1]['gas_used'])
			f.write("{},{}\n".format(max_savings[i][0], pct_savings))

	with open('data/copy-size-distribution.csv', 'w') as f:
		f.write("\"copy size (32 bytes)\",\"number of occurances\"\n")
		for copy_size, num in sorted(copy_size_occurances.items(), key=lambda x: x[0]):
			f.write("{},{}\n".format(copy_size, num))

	# MCOPY savings for most popular contracts
	# not substantial enough to consider
	# savings_popular = sorted(result.items(), key=lambda x: x[1]['gas_used'])

if __name__ == "__main__":
	main()
