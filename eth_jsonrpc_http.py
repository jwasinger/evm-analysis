import requests

class EthRPCClient:
    def __init__(self, uri):
        self.rpcEndpoint = uri

    def __enter__(self):
        self.session = requests.Session()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def debugAccountRange(self, startHash, count) -> ([(str, bool)], str):
        payload = {
            'method': 'debug_accountRange',
            'params': ["latest", startHash, count, True, True, True],
            'jsonrpc': '2.0',
            "id": 0,
        }

        response = self.session.post(self.rpcEndpoint, json=payload)
        result = response.json()['result']

        zeroCodeHash = 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
        result_accounts = []

        for address, account in zip(result['accounts'].keys(), result['accounts'].values()):
            result_accounts.append((address, account['codeHash'] != zeroCodeHash))

        if not 'next' in result:
            return (result_accounts, None)
        else:
            return (result_accounts, result['next'])
