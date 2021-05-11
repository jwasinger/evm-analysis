import requests

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

def parse_trace(steps: []):
    prev_step = None

    for step in steps:
            if step['op'] == 'MSTORE':
                import pdb; pdb.set_trace()
                if prev_step and prev_step['op'] == 'MLOAD':
                        import pdb; pdb.set_trace()
                        foo = 'bar'

            if not 'PUSH' in step['op']:
                prev_step = step

# def trace_tx_history(tracer: EVMTracer, start_block: int, end_block_int):
#     pass

def trace_block(block_number: int):
    block = rpc_ethGetBlockByNumber(block_number)

    if len(block['transactions']) > 0:
            for tx_hash in block['transactions']:
                    tx_trace = rpc_debugTraceTransaction(tx_hash)
                    if tx_trace and tx_trace['structLogs'] != []:
                        parse_trace(tx_trace['structLogs'])

def trace_block_range(start: int, end: int):
    for block_number in range(start, end+1):
            trace_block(block_number)

def main():
    # trace_result = trace_tx_history(trace, 10000000, 11000000)
    # trace_block(1000)
    trace_block_range(100000, 110000)

if __name__ == "__main__":
        main()
