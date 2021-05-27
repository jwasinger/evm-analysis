// Copyright 2017 The go-ethereum Authors
// This file is part of the go-ethereum library.
//
// The go-ethereum library is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// The go-ethereum library is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with the go-ethereum library. If not, see <http://www.gnu.org/licenses/>.

// callTracer is a full blown transaction tracer that extracts and reports all
// the internal calls made by a transaction, along with any useful information.
{
	// callstack is the current recursive call stack of the EVM execution.
	callstack: [{to: null, memcopyState: {candidates: [], copies: [], prevOp: null}}],
	hasCopies: false,

	// descended tracks whether we've just descended from an outer transaction into
	// an inner call.
	descended: false,
  opcodes: {
	"ADD": [-2, 1],
	"MUL": [-2, 1],
	"SUB": [-2, 1],
	"DIV": [-2, 1],
	"SDIV": [-2, 1],
	"MOD": [-2, 1],
	"SMOD": [-2, 1],
	"ADDMOD": [-3, 1],
	"MULMOD": [-3, 1],
	"EXP": [-2, 1],
	"LT": [-2, 1],
	"GT": [-2, 1],
	"SLT": [-2, 1],
	"SGT": [-2, 1],
	"EQ": [-2, 1],
	"ISZERO": [-1, 1],
	"AND": [-2, 1],
	"OR": [-2, 1],
	"XOR": [-2, 1],
	"NOT": [-1, 1],
	"BYTE": [-2, 1],
	"SHL": [-2, 1],
	"SHR": [-2, 1],
	"SAR": [-2, 1],
	"SHA3": [-2, 1],
	"ADDRESS": [0, 1],
	"BALANCE": [-1, 1],
	"SELFBALANCE": [0, 1],
	"ORIGIN": [0, 1],
	"CALLER": [0, 1],
	"CALLVALUE": [0, 1],
	"CALLDATALOAD": [-1, 1],
	"CALLDATASIZE": [0, 1],
	"CALLDATACOPY": [-3, 0],
	"CODESIZE": [0, 1],
	"CODECOPY": [-3, 0],
	"GASPRICE": [0, 1],
	"EXTCODESIZE": [-1, 1],
	"EXTCODECOPY": [-4, 0],
	"RETURNDATASIZE": [0, 1],
	"RETURNDATACOPY": [-3, 0],
	"EXTCODEHASH": [-1, 1],
	"BLOCKHASH": [-1, 1],
	"COINBASE": [0, 1],
	"TIMESTAMP": [0, 1],
	"NUMBER": [0, 1],
	"DIFFICULTY": [0, 1],
	"GASLIMIT": [0, 1],
	"CHAINID": [0, 1],
	"POP": [-1, 0],
	"MLOAD": [-1, 1],
	"MSTORE": [-2, 0],
	"MSTORE8": [-2, 0],
	"SLOAD": [-1, 1],
	"SSTORE": [-2, 0],
	"JUMP": [-1, 0],
	"JUMPI": [-2, 0],
	"PC": [0, 1],
	"MSIZE": [-1, 1],
	"GAS": [0, 1],
	"JUMPDEST": [0, 0],
	"PUSH": [0, 1],
	"DUP": [0, 0],
	"SWAP": [0, 0],
	"LOG0": [-2, 0],
	"LOG1": [-3, 0],
	"LOG2": [-4, 0],
	"LOG3": [-5, 0],
	"LOG4": [-6, 0],
	"CREATE": [-3, 1],
	"CALL": [-7, 1],
	"CALLCODE": [-7, 1],
	"RETURN": [-2, 0],
	"DELEGATECALL": [-6, 1],
	"CREATE2": [-4, 1],
	"STATICCALL": [-6, 1],
	"REVERT": [-2, 0],
	"SELFDESTRUCT": [-1, 0],
	"SIGNEXTEND": [-2, 1],
	"STOP": [0, 0],
  },
  deepCopyStack: function(log) {
	var result = []
	for (var i = 0; i < log.stack.length(); i++) {
		result.push(log.stack.peek(i).toString(16))
	}

	return result
  },
  printStack: function(stack) {
    var result = "{"
    for (var i = 0; i < stack.length(); i++) {
      result += stack.peek(i).toString(16) + ","
    }
    result += "}"
    console.log(result)
  },
  stepCandidates: function(callState) {
	var opName = callState.memcopyState.prevOp.name

	if (opName.includes('PUSH')) {
		opName = 'PUSH'
	}

	var stackTaken = this.opcodes[opName][0]
	var stackLeft = this.opcodes[opName][1]
	var stackDelta = stackLeft + stackTaken

	var spliceAt = []
	var candidates = callState.memcopyState.candidates
	const MAX_STACK_SIZE = 1024

	for (var i = 0; i < candidates.length; i++) {
		if (candidates[i].idx + stackTaken < 0) {
			// candidate was an argument to this opcode
			spliceAt.push(i)
		} else {
			candidates[i].idx += stackDelta
		}
	}

	callState.memcopyState.candidates = candidates.filter(function(value, index) {
		for (var j = 0; j < spliceAt.length; j++) {
			if (spliceAt[j] == index) {
				return false
			}
		}

		return true

		// Array.prototype.includes doesn't exist :(
		// return spliceAt.includes(index)
	})
  },
  stepCandidatesDUP: function(callState) {
	  var opName = callState.memcopyState.prevOp.name
	  var dupCandidate = null
	  var candidates = callState.memcopyState.candidates
	  var dupN = parseInt(opName.replace('DUP', ''), 10)

	  for (var i = 0; i < candidates.length; i++) {
		if (candidates[i]['idx'] + 1 == dupN) {
			dupCandidate = i
		} else {
			candidates[i].idx++
		}
	  }

	  if (dupCandidate != null) {
		candidates.splice(dupCandidate, 1)
	  }
  },
  stepCandidatesSWAP: function(opName, callState) {
	  var candidates = callState.memcopyState.candidates
 	  var swapN = parseInt(opName.replace('SWAP', ''), 10)

	  for (var i = 0; i < candidates.length; i++) {
		  if (candidates[i]["idx"] == 0) {
			  candidates[i]["idx"] = swapN
		  } else if (candidates[i]["idx"] == swapN) {
			candidates[i]["idx"] = 0
		}
	  }
  },
  stepMSTORE: function(callState) {
	var candidates = callState.memcopyState.candidates
	var call_copies = callState.memcopyState.copies
	var offset = callState.memcopyState.prevOp.offset
	var spliceAt = []

	// delete any values that were arguments to this MSTORE, update the stack indexes of the others being tracked
	for (var i = 0; i < candidates.length; i++) {
		if (candidates[i]['idx'] == 1) {
			this.hasCopies = true
			call_copies.push({
				"srcOffset": candidates[i].offset,
				"srcPC": candidates[i].pc,
				"dstOffset": offset,
				"dstPC": callState.memcopyState.prevOp.pc
			})
			console.log("copied")

			spliceAt.push(i)
		} else if (candidates[i].idx == 0) {
			spliceAt.push(i)
		} else {
			candidates[i].idx -= 2
		}
	}

	callState.memcopyState.candidates = candidates.filter(function(value, index) {
		for (var j = 0; j < spliceAt.length; j++) {
			if (spliceAt[j] == index) {
				return false
			}
		}

		return true

		// Array.prototype.includes doesn't exist :(
		// return spliceAt.includes(index)
	})
  },
  stepMLOAD: function(log, callState) {
	var candidates = callState.memcopyState.candidates
	var value = log.stack.peek(0)
	var offset = callState.memcopyState.prevOp.offset
	var pc = callState.memcopyState.prevOp.pc
	var spliceAt = null

	// delete any copy candidates if they were an MLOAD argument
	for (var i = 0; i < candidates.length; i++) {
		if (candidates[i].idx == 0) {
			spliceAt = i
		}
	}

	if (spliceAt != null) {
		candidates.splice(spliceAt, 1)
	}

	candidates.push({"pc": pc, "offset": offset.toString(16), "value": value.toString(16), "idx": 0})
  },
  applyOpStateTransition: function (log, callState) {
	  var opName = callState.memcopyState.prevOp.name

	  if (opName == 'MLOAD') {
		this.stepMLOAD(log, callState)
	  } else if (opName  == 'MSTORE') {
		this.stepMSTORE(callState)
	  } else {
		  if (opName.includes('DUP')) {
			this.stepCandidatesDUP(callState)
		  } else if (opName.includes('SWAP')) {
			this.stepCandidatesSWAP(opName, callState)
		  } else {
			this.stepCandidates(callState)
		  }
	  }
  },

	// step is invoked for every opcode that the VM executes.
	step: function(log, db) {
		// Capture any errors immediately
		var error = log.getError();
		if (error !== undefined) {
			this.fault(log, db);
			return;
		}

		var op = log.op.toString();
		var syscall = (log.op.toNumber() & 0xf0) == 0xf0;

		if (log.op.toString().includes('STATICCALL')) {
			console.log(log.getDepth())
			console.log(log.op.toString())
			this.printStack(log.stack)
			console.log(this.callstack[this.callstack.length - 1].memcopyState.candidates)
		}

		// If a new contract is being created, add to the call stack
		if (syscall && (op == 'CREATE' || op == "CREATE2")) {
			var inOff = log.stack.peek(1).valueOf();
			var inEnd = inOff + log.stack.peek(2).valueOf();

			// Assemble the internal call report and store for completion
			var call = {
				type:    op,
				from:    toHex(log.contract.getAddress()),
				input:   toHex(log.memory.slice(inOff, inEnd)),
				gasIn:   log.getGas(),
				gasCost: log.getCost(),
				value:   '0x' + log.stack.peek(0).toString(16),
				memcopyState: {candidates: [], copies: [], prevOp: null}
			};
			this.callstack.push(call);
			this.descended = true
			return;
		}
		// If a contract is being self destructed, gather that as a subcall too
		if (syscall && op == 'SELFDESTRUCT') {
			var left = this.callstack.length;
			if (this.callstack[left-1].calls === undefined) {
				this.callstack[left-1].calls = [];
			}
			this.callstack[left-1].calls.push({
				type:    op,
				from:    toHex(log.contract.getAddress()),
				to:      toHex(toAddress(log.stack.peek(0).toString(16))),
				gasIn:   log.getGas(),
				gasCost: log.getCost(),
				value:   '0x' + db.getBalance(log.contract.getAddress()).toString(16)
			});
			return
		}
		// If a new method invocation is being done, add to the call stack
		if (syscall && (op == 'CALL' || op == 'CALLCODE' || op == 'DELEGATECALL' || op == 'STATICCALL')) {
			// Skip any pre-compile invocations, those are just fancy opcodes
			var to = toAddress(log.stack.peek(1).toString(16));
			if (isPrecompiled(to)) {
				return
			}
			var off = (op == 'DELEGATECALL' || op == 'STATICCALL' ? 0 : 1);

			var inOff = log.stack.peek(2 + off).valueOf();
			var inEnd = inOff + log.stack.peek(3 + off).valueOf();

			// Assemble the internal call report and store for completion
			var call = {
				type:    op,
				from:    toHex(log.contract.getAddress()),
				to:      toHex(to),
				input:   toHex(log.memory.slice(inOff, inEnd)),
				gasIn:   log.getGas(),
				gasCost: log.getCost(),
				outOff:  log.stack.peek(4 + off).valueOf(),
				outLen:  log.stack.peek(5 + off).valueOf(),
				memcopyState: {candidates: [], copies: [], prevOp: null}
			};
			if (op != 'DELEGATECALL' && op != 'STATICCALL') {
				call.value = '0x' + log.stack.peek(2).toString(16);
			}

			// set the prevOp for this callFrame as this `CALL*` before adding a new frame
			this.callstack[this.callstack.length - 1].memcopyState.prevOp = {'name': op, offset: log.stack.peek(0), pc: log.getPC(), stack: this.deepCopyStack(log)}
			this.callstack.push(call);
			this.descended = true
			return;
		}
		// If we've just descended into an inner call, retrieve it's true allowance. We
		// need to extract if from within the call as there may be funky gas dynamics
		// with regard to requested and actually given gas (2300 stipend, 63/64 rule).
		if (this.descended) {
			if (log.getDepth() >= this.callstack.length) {
				this.callstack[this.callstack.length - 1].gas = log.getGas();
			} else {
				// TODO(karalabe): The call was made to a plain account. We currently don't
				// have access to the true gas amount inside the call and so any amount will
				// mostly be wrong since it depends on a lot of input args. Skip gas for now.
			}
			this.descended = false;
                        console.log("entered call " + log.getDepth())
		}
		// If an existing call is returning, pop off the call stack
		if (syscall && op == 'REVERT') {
			this.callstack[this.callstack.length - 1].error = "execution reverted";
			return;
		}
		if (log.getDepth() == this.callstack.length - 1) {
			// Pop off the last call and get the execution results
			var call = this.callstack.pop();

			if (call.type == 'CREATE' || call.type == "CREATE2") {
				// If the call was a CREATE, retrieve the contract address and output code
				call.gasUsed = '0x' + bigInt(call.gasIn - call.gasCost - log.getGas()).toString(16);
				delete call.gasIn; delete call.gasCost;

				var ret = log.stack.peek(0);
				if (!ret.equals(0)) {
					call.to     = toHex(toAddress(ret.toString(16)));
					call.output = toHex(db.getCode(toAddress(ret.toString(16))));
				} else if (call.error === undefined) {
					call.error = "internal failure"; // TODO(karalabe): surface these faults somehow
				}
			} else {
				// If the call was a contract call, retrieve the gas usage and output
				if (call.gas !== undefined) {
					call.gasUsed = '0x' + bigInt(call.gasIn - call.gasCost + call.gas - log.getGas()).toString(16);
				}
				var ret = log.stack.peek(0);
				if (!ret.equals(0)) {
					call.output = toHex(log.memory.slice(call.outOff, call.outOff + call.outLen));
				} else if (call.error === undefined) {
					call.error = "internal failure"; // TODO(karalabe): surface these faults somehow
				}
				delete call.gasIn; delete call.gasCost;
				delete call.outOff; delete call.outLen;
			}
			if (call.gas !== undefined) {
				call.gas = '0x' + bigInt(call.gas).toString(16);
			}
			// Inject the call into the previous one
			var left = this.callstack.length;
			if (this.callstack[left-1].calls === undefined) {
				this.callstack[left-1].calls = [];
			}
			this.callstack[left-1].calls.push(call);

                        console.log("exited call " + log.getDepth())
		}



		var curCall = this.callstack[this.callstack.length - 1]
		if (curCall.memcopyState.prevOp != null) {
			//console.log(curCall.memcopyState.candidates)
			this.applyOpStateTransition(log, curCall)

/*
			console.log("prevOp:")
			console.log(curCall.memcopyState.prevOp.name)
			console.log(curCall.memcopyState.candidates)
			console.log("end")
*/

			for (var i = 0; i < curCall.memcopyState.candidates.length; i++) {
				var candidate = curCall.memcopyState.candidates[i];
				var candidate_val = candidate.value
				var stack_val = log.stack.peek(candidate.idx).toString(16)

				if (candidate_val != stack_val) {
					console.log(curCall.memcopyState.prevOp.name)
					console.log("mismatch: expected " + candidate_val + " != actual " + stack_val + ")")
					console.log("candidate index: " + candidate.idx)
					console.log("stack before: ")
					console.log(curCall.memcopyState.prevOp.stack)
					console.log("stack after: ")
					this.printStack(log.stack)
					console.log("pc: ")
					console.log(log.getPC())
					throw("fuck")
				}
			}
		}

		if (op == 'MLOAD') {
			curCall.memcopyState.prevOp = {'name': op, offset: log.stack.peek(0), pc: log.getPC(), stack: this.deepCopyStack(log)}

		} else if (op == 'MSTORE') {
			curCall.memcopyState.prevOp = {'name': op, value: log.stack.peek(0), offset: log.stack.peek(1), pc: log.getPC(), stack: this.deepCopyStack(log)}
		} else {
			curCall.memcopyState.prevOp = {'name': op, pc: log.getPC(), stack: this.deepCopyStack(log)}
		}
	},

	// fault is invoked when the actual execution of an opcode fails.
	fault: function(log, db) {
		// If the topmost call already reverted, don't handle the additional fault again
		if (this.callstack[this.callstack.length - 1].error !== undefined) {
			return;
		}
		// Pop off the just failed call
		var call = this.callstack.pop();
		call.error = log.getError();

		// Consume all available gas and clean any leftovers
		if (call.gas !== undefined) {
			call.gas = '0x' + bigInt(call.gas).toString(16);
			call.gasUsed = call.gas
		}
		delete call.gasIn; delete call.gasCost;
		delete call.outOff; delete call.outLen;

		// Flatten the failed call into its parent
		var left = this.callstack.length;
		if (left > 0) {
			if (this.callstack[left-1].calls === undefined) {
				this.callstack[left-1].calls = [];
			}
			this.callstack[left-1].calls.push(call);
			return;
		}
		// Last call failed too, leave it in the stack
		this.callstack.push(call);
	},

	// result is invoked when all the opcodes have been iterated over and returns
	// the final result of the tracing.
	result: function(ctx, db) {
		var result = { };
		if (this.hasCopies) {
			var result = {
				type:    ctx.type,
				from:    toHex(ctx.from),
				to:      toHex(ctx.to),
				value:   '0x' + ctx.value.toString(16),
				gas:     '0x' + bigInt(ctx.gas).toString(16),
				gasUsed: '0x' + bigInt(ctx.gasUsed).toString(16),
				input:   toHex(ctx.input),
				output:  toHex(ctx.output),
				time:    ctx.time,
			};
			if (this.callstack[0].calls !== undefined) {
				result.calls = this.callstack[0].calls;
			}

/*
			if (this.callstack[0].calls !== undefined && this.hasCopies) {
				console.log("shitty shit shit")
				console.log(this.callstack[0].memcopyState.copies);
				result.calls = this.callstack[0].calls;
			}
*/
			result.copies = this.callstack[0].memcopyState.copies

			if (this.callstack[0].error !== undefined) {
				result.error = this.callstack[0].error;
			} else if (ctx.error !== undefined) {
				result.error = ctx.error;
			}
			if (result.error !== undefined && (result.error !== "execution reverted" || result.output ==="0x")) {
				delete result.output;
			}
			console.log(result)
		}
		this.hasCopies = false

		// return this.finalize(result);
		return result
	},

	// finalize recreates a call object using the final desired field oder for json
	// serialization. This is a nicety feature to pass meaningfully ordered results
	// to users who don't interpret it, just display it.
	finalize: function(call) {
		var sorted = {
			type:    call.type,
			from:    call.from,
			to:      call.to,
			value:   call.value,
			gas:     call.gas,
			gasUsed: call.gasUsed,
			input:   call.input,
			output:  call.output,
			error:   call.error,
			time:    call.time,
			calls:   call.calls,
		}
		for (var key in sorted) {
			if (sorted[key] === undefined) {
				delete sorted[key];
			}
		}
		if (sorted.calls !== undefined) {
			for (var i=0; i<sorted.calls.length; i++) {
				sorted.calls[i] = this.finalize(sorted.calls[i]);
			}
		}
		return sorted;
	}
}
