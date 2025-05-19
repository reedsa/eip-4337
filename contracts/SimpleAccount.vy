# @version ^0.4.1

# ERC-4337 Simple Account implementation
# This is a minimal implementation that allows an owner to execute transactions
# through the EntryPoint contract

struct UserOperation:
    sender: address
    nonce: uint256
    initCode: Bytes[256]
    callData: Bytes[256]
    accountGasLimits: bytes32  # packed verificationGasLimit and callGasLimit
    preVerificationGas: uint256
    gasFees: bytes32  # packed maxFeePerGas and maxPriorityFeePerGas
    paymasterAndData: Bytes[256]
    signature: Bytes[256]

interface EntryPoint:
    def handleOps(ops: UserOperation[1], beneficiary: address): nonpayable
    def getNonce(account: address, key: uint256) -> uint256: view
    def balanceOf(account: address) -> uint256: view

event AccountExecuted:
    target: address
    value: uint256
    data: Bytes[256]

event SignerCheck:
    signer: address
    owner: address

owner: public(address)
entryPoint: public(EntryPoint)

@deploy
def __init__(_owner: address, _entryPoint: address):
    self.owner = _owner
    self.entryPoint = EntryPoint(_entryPoint)

@external
@payable
def __default__():
    pass

@external
def validateUserOp(userOp: UserOperation, userOpHash: bytes32, missingFunds: uint256) -> bytes32:
    # Verify the operation is from the EntryPoint
    assert msg.sender == self.entryPoint.address, "Not from EntryPoint"
    
    # Extract signature components
    r: bytes32 = extract32(userOp.signature, 0)
    s: bytes32 = extract32(userOp.signature, 32)
    v: uint8 = convert(slice(userOp.signature, 64, 1), uint8)
    
    # Recover the signer
    signer: address = ecrecover(userOpHash, v, r, s)
    
    # Debug log the signer and owner
    log SignerCheck(signer=signer, owner=self.owner)
    
    # Verify the signer is the owner
    assert signer == self.owner, "Invalid signature"
    
    # Return empty bytes32 as we don't need any context
    return empty(bytes32)

@external
def execute(target: address, amount: uint256, data: Bytes[256]):
    # Verify the operation is from the EntryPoint
    assert msg.sender == self.entryPoint.address, "Not from EntryPoint"
    
    # Execute the call
    raw_call(target, data, value=amount, gas=msg.gas)
    
    # Log the execution
    log AccountExecuted(target=target, value=amount, data=data)

@external
def executeBatch(targets: address[10], amounts: uint256[10], data: Bytes[256]):
    # Verify the operation is from the EntryPoint
    assert msg.sender == self.entryPoint.address, "Not from EntryPoint"
    
    # Execute each call in the batch
    for i: uint256 in range(10):
        if targets[i] == empty(address):
            break
        # Extract the data for this call from the concatenated data
        start: uint256 = i * 256
        end: uint256 = start + 256
        call_data: Bytes[256] = slice(data, start, 256)
        raw_call(targets[i], call_data, value=amounts[i], gas=msg.gas)
        log AccountExecuted(target=targets[i], value=amounts[i], data=call_data)

@external
def getNonce() -> uint256:
    return staticcall self.entryPoint.getNonce(self, 0)

@external
def getDeposit() -> uint256:
    return staticcall self.entryPoint.balanceOf(self)
