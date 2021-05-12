import requests
import math

jsonrpc_endpoint='http://localhost:8545'

def rpc_ethGetBlockNumber():
        block_num_hex = hex(block)
        payload = {
            'method': 'eth_getBlockNumber',
            'params': [],
            'jsonrpc': '2.0',
            "id": 0,
        }
        response = requests.post(jsonrpc_endpoint, json=payload).json()
        return response

def rpc_ethGetBlockByNumber(block: int):
        block_num_hex = hex(block)
        payload = {
            'method': 'eth_getBlockByNumber',
            'params': [block_num_hex, False],
            'jsonrpc': '2.0',
            "id": 0,
        }
        response = requests.post(jsonrpc_endpoint, json=payload).json()
        return response['result']

def rpc_debugTraceTransaction(tx_hash):
        payload = {
            'method': 'debug_traceTransaction',
            'params': [tx_hash],
            'jsonrpc': '2.0',
            "id": 0,
        }
        response = requests.post(jsonrpc_endpoint, json=payload).json()

        if not 'result' in response:
            return None

        return response['result']

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

# given an execution trace:
#   identify cases where MLOAD and MSTORE are called consecutively and used to copy a word of memory
def parse_trace_mcopy(steps: []):
    prev_step = None
    result = []

    for step in steps:
            if step['op'] == 'MSTORE':
                if prev_step and prev_step['op'] == 'MLOAD':
                    result.append(len(step['memory']))

            if not 'PUSH' in step['op']:
                prev_step = step

    return (steps[0]['gas'] - steps[-1]['gas'], result)

# def trace_tx_history(tracer: EVMTracer, start_block: int, end_block_int):
#     pass

def trace_block(block_number: int):
    block = rpc_ethGetBlockByNumber(block_number)

    # result is lookup of tx_hash: (total_gas_used, [msize]) where size of memory when each copy was performed
    # result = {}

    result = {}

    if len(block['transactions']) > 0:
            for tx_hash in block['transactions']:
                    tx_trace = rpc_debugTraceTransaction(tx_hash)
                    if tx_trace and tx_trace['structLogs'] != []:
                        gas_used, mem_size_at_copies = parse_trace_mcopy(tx_trace['structLogs'])
                        if mem_size_at_copies:
                            result[tx_hash] = {
                                    'gas_used': gas_used,
                                    'mem_size_at_copies': mem_size_at_copies,
                                    'savings': calc_mcopy_savings(gas_used, mem_size_at_copies)}
                            print("found savings of {}%".format(result[tx_hash]['savings'] * 100))
    return result


def trace_block_range(start: int, end: int):
    for block_number in range(start, end+1):
            trace_block(block_number)

def main():
    # trace_result = trace_tx_history(trace, 10000000, 11000000)
    # trace_block(1000)
    trace_block_range(10537502, 10558149)

if __name__ == "__main__":
        main()
