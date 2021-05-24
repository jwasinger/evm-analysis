{
  mload_vals: [],
  result_copies: [],
  strip: function(x) {
    return x.replace(/^0+/, '')
  },
  printStack: function(stack) {
    console.log("{")
    for (var i = 0; i < stack.length(); i++) {
      console.log(stack.peek(i).toString())
      console.log(",")
    }
    console.log("}")
  },
  ops: {
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
  },
  deepCopyStack: function(log) {
	var result = []
	for (var i = 0; i < log.stack.length(); i++) {
		result.push(log.stack.peek(i))
	}

	return result
  },
  state: {
	  call_frame_state: [{copies: [], candidates: [], prev_op: null}],
	  last_call_depth: 1,
  },
  stepCandidates: function(opName) {
	var stackTaken = this.ops[opName][0]
	var stackLeft = this.ops[opName][1]
	var stackDelta = stackLeft + stackTaken

	var spliceAt = []
	var candidates = this.state.call_frame_state[0].candidates
	const MAX_STACK_SIZE = 1024

	for (var i = 0; i < candidates.length; i++) {
		if (candidates[i].idx + stackTaken < 0) {
			// candidate was an argument to this opcode
			spliceAt.push(i)
		} else {
			candidates[i].idx += stackDelta
		}
	}

	this.state.call_frame_state[0].candidates = candidates.filter(function(value, index) {
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
  stepCandidatesDUP: function(dupN) {
	  var dupCandidate = null
	  var candidates = this.state.call_frame_state[0].candidates

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
  stepCandidatesSWAP: function(swapN) {
	  var candidates = this.state.call_frame_state[0].candidates
	  for (var i = 0; i < candidates.length; i++) {
		  if (candidates[i]["idx"] == 0) {
			  candidates[i]["idx"] = swapN
		  } else if (candidates[i]["idx"] == swapN) {
			candidates[i]["idx"] = 0
		}
	  }
  },
  stepMSTORE: function(log) {
	// record the candidate as a copy if the value stored was previously MLOADed
	var call_frame_state = this.state.call_frame_state[0]
	var candidates = call_frame_state.candidates
	var call_copies = call_frame_state.copies

	var offset = parseInt(call_frame_state.prev_op.stack[0], 10);
	var spliceAt = []

	for (var i = 0; i < candidates.length; i++) {
		if (candidates[i]['idx'] == 1) {
			call_copies.push({
				"address": toHex(log.contract.getAddress()),
				"srcOffset": candidates[i]['offset'],
				"srcPC": candidates[i].pc,
				"dstOffset": offset,
				"dstPC": call_frame_state.prev_op.pc
			})

			spliceAt.push(i)
		} else if (candidates[i].idx == 0) {
			spliceAt.push(i)
		} else {
			candidates[i]['idx'] -= 2
		}
	}

	this.state.call_frame_state[0].candidates = candidates.filter(function(value, index) {
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
  stepMLOAD: function(log) {
	var prev_op_stack = this.state.call_frame_state[0].prev_op.stack
	var cur_stack = log.stack
	var offset = parseInt(prev_op_stack[0], 10);
	var value = cur_stack.peek(0).toString(10)
	var pc = this.state.call_frame_state[0].prev_op.pc
	var candidates = this.state.call_frame_state[0].candidates

	var spliceAt = null

	for (var i = 0; i < candidates.length; i++) {
		if (candidates[i].idx == 0) {
			spliceAt = i
		}
	}

	if (spliceAt != null) {
		candidates.splice(spliceAt, 1)
	}

	this.state.call_frame_state[0].candidates.push({"pc": pc, "offset": offset, "value": value, "idx": 0})
  },
  applyOpStateTransition: function (op, log) {
	  if (op.name == 'MLOAD') {
		this.stepMLOAD(log)
	  } else if (op.name == 'MSTORE') {
		this.stepMSTORE(log)
	  } else {
		  if (op.name.includes('DUP')) {
			var dupN = parseInt(op.name.replace('DUP', ''), 10)
			this.stepCandidatesDUP(dupN)
		  } else if (op.name.includes('SWAP')) {
			var swapN = parseInt(op.name.replace('SWAP', ''), 10)
			this.stepCandidatesSWAP(swapN)
		  } else {
			var opName = op.name
			if (opName.includes('PUSH')) {
				opName = 'PUSH'
			}

			this.stepCandidates(opName)
		  }
	  }
  },
  step: function (log, db) {
	var opName = log.op.toString()

/*
	if (opName == "STOP") {
		if (this.state.call_frame_state[0].copies.length > 0) {
			this.result_copies.push(this.state.call_frame_state[0].copies)
		}
		this.state.call_frame_state.shift()
		return
	}
*/

	if (this.state.last_call_depth > log.getDepth()) {
		console.log("exited message call")
		// TODO distinguish between RETURN and REVERT

		this.state.last_call_depth = log.getDepth()
		var call_frame_state = this.state.call_frame_state.shift()

		if (call_frame_state.copies.length > 0) {
			this.result_copies.push(call_frame_state.copies)
		}
	} else if (this.state.last_call_depth < log.getDepth()) {
		console.log("entered message call")
		this.state.last_call_depth = log.getDepth()
		this.state.call_frame_state.unshift({
			copies: [],
			candidates: [],
			prev_op: null
		})
	}


	var prevOp = this.state.call_frame_state[0].prev_op
        if (log.getPC() == 10918) {
		console.log(prevOp.name)
		console.log(this.state.call_frame_state[0].candidates)
	}

	if (prevOp != null) {
		this.applyOpStateTransition(prevOp, log)
	}

	for (var i = 0; i < this.state.call_frame_state[0].candidates.length; i++) {
		var candidate = this.state.call_frame_state[0].candidates[i];
		var candidate_val = candidate.value
		// var stack_val = this.state.call_frame_state[0].prev_op.stack[candidate.idx]
		var stack_val = log.stack.peek(candidate.idx).toString(10)

		if (candidate_val != stack_val) {
			console.log(prevOp.name)
			console.log("mismatch: " + candidate_val + " != expected (" + stack_val + ")")
			console.log("stack before: ")
			console.log(this.state.call_frame_state[0].prev_op.stack)
			console.log("stack after: ")
			this.printStack(log.stack)
			console.log(this.state.call_frame_state[0].copies)
			throw("fuck")
		}
	}
	//console.log(this.state.call_frame_state[0].candidates)

	// TODO check that the stack values for each candidate idx match the recorded values after the step state transition is applied
	this.state.call_frame_state[0].prev_op = {'name': opName, stack: this.deepCopyStack(log), pc: log.getPC()}
  },
  result: function (ctx, db) {
	  /*
    if (this.state.cur_call_copies[0].length != 0) {
	console.log(this.state.cur_call_copies)
	throw("bad")
    }
    */

    return {"copies": this.result_copies};
  },
  fault: function (log, db) {},
}
