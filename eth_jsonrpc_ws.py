import asyncio
import websockets
import json

class EthRPCClient:
    def __init__(self, uri):
        self.uri = uri

    async def __aenter__(self):
            self.websocket = await asyncio.wait_for(websockets.connect(self.uri, max_size=None), timeout=10)

    async def __aexit__(self, exc_type, exc, tb):
        await self.websocket.close()

    async def eth_blockNumber(self):
        payload = {
            'method': 'eth_blockNumber',
            'params': [],
            'jsonrpc': '2.0',
            "id": 0,
        }

        await self.websocket.send(json.dumps(payload))
        result = await self.websocket.recv()
        result = json.loads(result)
        return result['result']

    async def ethGetBlockByNumber(self, block: int):
        block_num_hex = hex(block)
        payload = {
            'method': 'eth_getBlockByNumber',
            'params': [block_num_hex, False],
            'jsonrpc': '2.0',
            "id": 0,
        }

        await self.websocket.send(json.dumps(payload))
        result = await self.websocket.recv()
        result = json.loads(result)
        return result['result']

    async def debugAccountRangeAt(self, startHash, count) -> ([(str, bool)], str):
        payload = {
            'method': 'debug_accountRange',
            'params': ["latest", startHash, count, True, True, True],
            'jsonrpc': '2.0',
            "id": 0,
        }
        await self.websocket.send(json.dumps(payload))
        result = await asyncio.wait_for(self.websocket.recv(), timeout=60)
        result = json.loads(result)['result']

        zeroCodeHash = 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
        result_accounts = []

        for address, account in zip(result['accounts'].keys(), result['accounts'].values()):
            result_accounts.append((address, account['codeHash'] != zeroCodeHash))

        if not 'next' in result:
            return (result_accounts, None)
        else:
            return (result_accounts, result['next'])

    async def debugTraceTransaction(self, tx_hash, tracer_script=None):
        payload = None

        if tracer_script:
            payload = {
                'method': 'debug_traceTransaction',
                'params': [tx_hash, {'tracer': tracer_script, "timeout": "500s"}],
                'jsonrpc': '2.0',
                "id": 0,
            }
        else:
            payload = {
                'method': 'debug_traceTransaction',
                'params': [tx_hash],
                'jsonrpc': '2.0',
                "id": 0,
            }

        await self.websocket.send(json.dumps(payload))

        try:
            result = await asyncio.wait_for(self.websocket.recv(), timeout=60)
        except Exception as e:
            return None

        result = json.loads(result)

        if not 'result' in result:
            return None
        return result['result']

