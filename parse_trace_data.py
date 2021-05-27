import sys, json, re

# return a map of contract_address: (copy count, gas spent), include reverted calls
# TODO figure out how to make the tracer emit gas spent in each call frame (without including internal calls)
def parse_contract_copies(tx_trace):
	result = {}
	result[tx_trace['to']] = { 'copy_count': len(tx_trace['copies']), 'gas_usage': 0}
	import pdb; pdb.set_trace()

	for call in tx_trace['calls']:
		if call['to'] in result:
			result[call['to']]['copy_count'] += len(call['memcopyState']['copies']) 
		else:
			result[call['to']] = {'copy_count': len(call['memcopyState']['copies']), 'gas_usage': 0}

	return result

def parse_consecutive_copies(tx_trace):
	import pdb; pdb.set_trace()

def main():
	trace_file = sys.argv[1]
	trace_lines = None

	contract_copies = {}
	copy_size_frequencies = {}

	with open(trace_file) as f:
		trace_lines = f.readlines()

	cur_tx = None
	cur_block = None

	i = 0
	tx = None
	while True:
		line = trace_lines[i]
		if line.startswith('tx: '):
			tx = line[4:]

			if i + 1 >= len(trace_lines):
				break
			elif trace_lines[i + 1] == 'error':
				i += 1
			elif trace_lines[i + 1].startswith("{"):
				trace_result = json.loads(trace_lines[i + 1].replace("'", '"').replace('None', '"None"'))
				copies = parse_contract_copies(trace_result)
				import pdb; pdb.set_trace()
				i += 1

		i += 1

if __name__ == "__main__":
	main()
