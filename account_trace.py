#!/usr/bin/env python

import asyncio
import websockets
import json
import sys

from eth_jsonrpc_http import EthRPCClient

async def main():
    uri = "http://localhost:8545"

    rpcClient = EthRPCClient(uri)
    with rpcClient:
        nxt = '0x00'
        while True:
                result = None
                result = rpcClient.debugAccountRange(nxt, 128)

                accounts = result[0]
                for (account, hasCode) in accounts:
                    print(account + "," + str(int(hasCode)))

                nxt = result[1]
                print(nxt, file=sys.stderr)
                if not nxt:
                        break

asyncio.get_event_loop().run_until_complete(main())
