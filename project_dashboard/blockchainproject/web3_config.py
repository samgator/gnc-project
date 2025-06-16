from web3 import Web3
from eth_account import Account
import json
import yaml
import os

# Load configuration from YAML file
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

config = load_config()

# Initialize Web3 with Sepolia testnet
INFURA_PROJECT_ID = config.get('web3', {}).get('infura_project_id', '')
SEPOLIA_RPC_URL = f'https://sepolia.infura.io/v3/{INFURA_PROJECT_ID}'
w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))

# ERC20 Token ABI (minimal for balance and transfer)
TOKEN_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

# Token contract address from config
TOKEN_CONTRACT_ADDRESS = config.get('web3', {}).get('token_contract_address', '')

# Initialize token contract
try:
    token_contract = w3.eth.contract(
        address=Web3.to_checksum_address(TOKEN_CONTRACT_ADDRESS) if TOKEN_CONTRACT_ADDRESS else None,
        abi=TOKEN_ABI
    )
except Exception as e:
    print(f"Error initializing token contract: {e}")
    token_contract = None

def get_token_balance(address):
    """Get token balance for an address"""
    try:
        if not w3.is_connected():
            return 0, "Not connected to Ethereum network"
        
        if not token_contract:
            return 0, "Token contract not initialized"
        
        # Convert address to checksum format
        checksum_address = Web3.to_checksum_address(address)
        
        # Get balance in wei
        balance_wei = token_contract.functions.balanceOf(checksum_address).call()
        
        # Convert from wei to tokens (18 decimals)
        balance = balance_wei / 10**18
        
        return balance, None
    except Exception as e:
        return 0, str(e)

def send_tokens(from_address, to_address, amount, private_key):
    """Send tokens from one address to another"""
    try:
        if not w3.is_connected():
            raise Exception("Not connected to Ethereum network")
        
        if not token_contract:
            raise Exception("Token contract not initialized")
        
        # Convert addresses to checksum format
        from_address = Web3.to_checksum_address(from_address)
        to_address = Web3.to_checksum_address(to_address)
        
        # Get the nonce
        nonce = w3.eth.get_transaction_count(from_address)
        
        # Build the transaction
        transaction = token_contract.functions.transfer(
            to_address,
            amount
        ).build_transaction({
            'from': from_address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign the transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        
        # Send the transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return receipt, None
    except Exception as e:
        return None, str(e) 