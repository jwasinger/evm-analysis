import requests
import math
import os
import json

jsonrpc_endpoint='http://localhost:8545'
session = requests.Session()

def rpc_ethGetBlockNumber():
        block_num_hex = hex(block)
        payload = {
            'method': 'eth_getBlockNumber',
            'params': [],
            'jsonrpc': '2.0',
            "id": 0,
        }
        response = session.post(jsonrpc_endpoint, json=payload)
        return response.json()

def rpc_ethGetBlockByNumber(block: int):
        block_num_hex = hex(block)
        payload = {
            'method': 'eth_getBlockByNumber',
            'params': [block_num_hex, False],
            'jsonrpc': '2.0',
            "id": 0,
        }
        response = session.post(jsonrpc_endpoint, json=payload)
        return response.json()['result']

def rpc_debugTraceTransaction(tx_hash):
        payload = {
            'method': 'debug_traceTransaction',
            'params': [tx_hash],
            'jsonrpc': '2.0',
            "id": 0,
        }
        response = session.post(jsonrpc_endpoint, json=payload)

        if not 'result' in response:
            return None

        return response.json()['result']

MCOPY_COST_1WORD = 1
G_COST_VERYLOW = 3

def memory_cost(memory_size):
    return memory_size * G_COST_VERYLOW + int(math.floor(memory_size ** 2 / 512))

def calc_mcopy_savings(gas_used, mem_size_at_copies):
    new_gas_used = gas_used

    # TODO: consider case where the copy expands memory
    for memsize in mem_size_at_copies:
        # subtract the cost of PUSH + PUSH + MLOAD + PUSH + MSTORE
        new_gas_used -= memory_cost(memsize) * 2 * G_COST_VERYLOW + G_COST_VERYLOW * 3

        # add cost of MCOPY (PUSH + MCOPY_COST_1WORD)
        new_gas_used += MCOPY_COST_1WORD + G_COST_VERYLOW

    return (gas_used - new_gas_used) / gas_used

# given an EVM execution trace:
#   search for memory copying: case when execution flow is ...,MLOAD,PUSH,MSTORE,...
#   return estimated savings and information about where copies occuried, EVM memory size at copy
def parse_trace_mcopy(steps: []):
    result_memory_size = []
    result_copies_pcs = []
    last_two_ops = []

    for idx, step in enumerate(steps):
            if step['op'] == 'MSTORE' and len(last_two_ops) == 2 and 'PUSH' in last_two_ops[0] and last_two_ops[1] == 'MLOAD':
                result_memory_size.append(len(step['memory']))
                result_copies_pcs.append(step['pc'])

            last_two_ops.insert(0, step['op'])
            last_two_ops = last_two_ops[:2]

    return (steps[0]['gas'] - steps[-1]['gas'], result_memory_size, result_copies_pcs)

def trace_block(block_number: int):
    block = rpc_ethGetBlockByNumber(block_number)

    # result is lookup of tx_hash: (total_gas_used, [msize]) where size of memory when each copy was performed
    # result = {}

    result = {}

    print("tracing block ", block_number)
    if len(block['transactions']) > 0:
            for tx_hash in block['transactions']:
                    tx_trace = rpc_debugTraceTransaction(tx_hash)
                    if tx_trace and tx_trace['structLogs'] != []:
                        gas_used, mem_size_at_copies, pcs_at_copies = parse_trace_mcopy(tx_trace['structLogs'])
                        if mem_size_at_copies:
                            result[tx_hash] = {
                                    'gas_used': gas_used,
                                    'mem_size_at_copies': mem_size_at_copies,
                                    'pcs_at_copies': pcs_at_copies,
                                    'savings': calc_mcopy_savings(gas_used, mem_size_at_copies)}
                            print("found savings of {}%".format(result[tx_hash]['savings'] * 100))
    return result


def trace_block_range(output_folder: str, start: int, end: int):
    for block_number in range(start, end+1):
            block_result = trace_block(block_number)
            with open(os.path.join(output_folder, "block{}.json".format(block_number)), 'w') as f:
                f.write(json.dumps(block_result))

def main():
    trace_block_range('db', 10537502, 10558149)

if __name__ == "__main__":
        main()
