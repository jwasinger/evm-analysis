# EVM Memory Copying Tracer

A utility for identifying all EVM memory copies for ranges of past blocks.


## Usage

* Have a Geth node synced with the necessary data available over Websocket on `localhost:8546`

* Setup local python env: `pipenv shell`

* Trace block ranges and gather data about memory copying: `python3 trace.py startblocknumber endblocknumber`

The json trace object reported for each transaction containing memory copies follows the form `[[{"srcOffset": Number, "dstOffset": Number, "srcPC": Number, "dstPC": Number, "address": HexString}, ...], [...], ...]`

where `srcOffset` and `dstOffset` represent the memory offset a value was loaded from and then stored to, `srcPC` and `dstPC` are the program counter for the source and destination `MLOAD`/`MSTORE` instructions and `address` is the contract being called.  Copies in the same message calls are grouped in sub-arrays in the output array.
