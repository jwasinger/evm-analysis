#!/usr/bin/env python

import asyncio
import websockets
import json
import sys

from eth_jsonrpc_ws import EthRPCClient

async def main():
    uri = "ws://localhost:8546"

    accounts = []
    rpcClient = EthRPCClient(uri)
    async with rpcClient:
        nxt = '0x00'
        while True:
                result = None
                result = await rpcClient.debugAccountRangeAt(nxt, 128)

                accounts += result[0]
                nxt = result[1]
                if not nxt:
                        break

        print("account address, account has code")
        for (account, hasCode) in accounts:
                print(account + "," + str(int(hasCode)))

asyncio.get_event_loop().run_until_complete(main())
