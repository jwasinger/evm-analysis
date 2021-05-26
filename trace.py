#!/usr/bin/env python

import asyncio
import websockets
import json
import sys

from eth_jsonrpc_ws import EthRPCClient

def parse_trace_mcopy(steps: []):
    # lookup of [(pc, offset)]
    mloads = []

    for idx, step in enumerate(steps):
        if step['op'] == 'MLOAD':
            offset = step['stack'][-1]
            mloads.append((step['pc'], int(offset, 16)))

    if not mloads:
        return None

    cur_consecutive = 1
    prev_offset = mloads[0][1]
    statr_pc = mloads[0][0]
    consecutive_counts = []

    for (pc, offset) in mloads:
        if offset == prev_offset + 32:
            cur_consecutive += 1
        else:
            prev_offset = offset
            if cur_consecutive > 1:
                consecutive_counts.append((start_pc, cur_consecutive))

            start_pc = pc
            cur_consecutive = 1

    return consecutive_counts 

mcopy_trace_script = ""
with open("call_tracer.js") as f:
    mcopy_trace_script = f.read()

def count_consecutive(trace_result):
        print(trace_result)

async def trace_block(rpcClient, block_number: int):
    block = await rpcClient.ethGetBlockByNumber(block_number)

    # result is lookup of tx_hash: (total_gas_used, [msize]) where size of memory when each copy was performed
    # result = {}

    result = {}

    print("block:", block_number)
    if 'transactions' in block and len(block['transactions']) > 0:
            for tx_hash in block['transactions']:
                    if tx_hash != "0xc5e46fe1aa43cf057e555166bc0ab6e7672e9a481f0d57ad346d2810d54bcba7":
                        continue

                    tx_trace = await rpcClient.debugTraceTransaction(tx_hash, mcopy_trace_script)
                    if 'calls' in tx_trace:
                        print("tx:", tx_hash)
                        sys.stdout.flush()
                        count_consecutive(tx_trace)
    return result


async def trace_block_range(rpcClient, start: int, end: int):
    for block_number in range(start, end+1):
            block_result = await trace_block(rpcClient, block_number)

async def main():
    uri = "ws://localhost:8546"

    if len(sys.argv) < 3:
      print("invoke like 'python3 trace.py startblocknum endblocknum'")
      sys.exit(1)

    start = int(sys.argv[1])
    end = int(sys.argv[2])

    rpcClient = EthRPCClient(uri)
    async with rpcClient:
        await trace_block_range(rpcClient, start, end)

asyncio.get_event_loop().run_until_complete(main())
