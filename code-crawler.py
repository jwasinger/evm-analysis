import sys
import base64
from eth_jsonrpc_http import EthRPCClient

def get_code(address, rpcClient):
    code_hex = rpcClient.ethGetCode(address)
    code_bytes = bytes.fromhex(code_hex[2:])
    result = base64.b64encode(code_bytes)
    return result

def main():
    url = "http://localhost:8545"
    if len(sys.argv) != 2:
        print("expects path to a csv where lines are account_address,has_code")

    source_file = sys.argv[1]
    rpcClient = EthRPCClient(url)
    with rpcClient:
            with open(source_file) as account_list_file:
                for idx, line in enumerate(account_list_file):
                    # print a csv of address, base64_encode(account_code)
                    line = line.strip('\n')
                    address, has_code = line.split(",")[0], line.split(",")[1]
                    if has_code != '0':
                        print(address, ", ", get_code(address, rpcClient).decode())

main()
