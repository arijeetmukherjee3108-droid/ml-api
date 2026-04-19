import os
import json
from web3 import Web3

class Web3Service:
    def __init__(self):
        self.rpc_url = os.getenv("SEPOLIA_RPC_URL", "https://eth-sepolia.g.alchemy.com/v2/your_alchemy_key_here")
        self.wallet_address = os.getenv("METAMASK_PUBLIC_ADDRESS")
        self.private_key = os.getenv("METAMASK_PRIVATE_KEY")
        self.contract_address = os.getenv("CONTRACT_ADDRESS")
        
        if self.rpc_url:
            self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Minimal, Gas-Optimized ABI with contentHash
        self.contract_abi = json.loads("""
[
	{
		"inputs": [
			{
				"internalType": "bytes32",
				"name": "_locationHash",
				"type": "bytes32"
			},
			{
				"internalType": "enum SafetyReports.IncidentType",
				"name": "_incidentType",
				"type": "uint8"
			},
			{
				"internalType": "bytes32",
				"name": "_contentHash",
				"type": "bytes32"
			},
			{
				"internalType": "bytes32",
				"name": "_resolutionToken",
				"type": "bytes32"
			}
		],
		"name": "fileReport",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_reportId",
				"type": "uint256"
			},
			{
				"internalType": "string",
				"name": "_secret",
				"type": "string"
			}
		],
		"name": "markResolved",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "uint256",
				"name": "reportId",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "bytes32",
				"name": "locationHash",
				"type": "bytes32"
			},
			{
				"indexed": false,
				"internalType": "enum SafetyReports.IncidentType",
				"name": "incidentType",
				"type": "uint8"
			},
			{
				"indexed": false,
				"internalType": "bytes32",
				"name": "contentHash",
				"type": "bytes32"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"name": "ReportFiled",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "uint256",
				"name": "reportId",
				"type": "uint256"
			}
		],
		"name": "ReportResolved",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_reportId",
				"type": "uint256"
			}
		],
		"name": "getReport",
		"outputs": [
			{
				"components": [
					{
						"internalType": "bytes32",
						"name": "locationHash",
						"type": "bytes32"
					},
					{
						"internalType": "enum SafetyReports.IncidentType",
						"name": "incidentType",
						"type": "uint8"
					},
					{
						"internalType": "bytes32",
						"name": "contentHash",
						"type": "bytes32"
					},
					{
						"internalType": "uint256",
						"name": "timestamp",
						"type": "uint256"
					},
					{
						"internalType": "bool",
						"name": "isActive",
						"type": "bool"
					},
					{
						"internalType": "bytes32",
						"name": "resolutionToken",
						"type": "bytes32"
					}
				],
				"internalType": "struct SafetyReports.Report",
				"name": "",
				"type": "tuple"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "reportCount",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "reports",
		"outputs": [
			{
				"internalType": "bytes32",
				"name": "locationHash",
				"type": "bytes32"
			},
			{
				"internalType": "enum SafetyReports.IncidentType",
				"name": "incidentType",
				"type": "uint8"
			},
			{
				"internalType": "bytes32",
				"name": "contentHash",
				"type": "bytes32"
			},
			{
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			},
			{
				"internalType": "bool",
				"name": "isActive",
				"type": "bool"
			},
			{
				"internalType": "bytes32",
				"name": "resolutionToken",
				"type": "bytes32"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]
""")

        if self.wallet_address and self.contract_address:
            self.contract = self.web3.eth.contract(address=self.contract_address, abi=self.contract_abi)

    def file_report_on_chain(self, lat: float, lng: float, incident_type: int, content_hash: bytes, resolution_token_hash: bytes) -> str:
        location_string = f"{lat},{lng}"
        location_hash = self.web3.keccak(text=location_string)
        
        nonce = self.web3.eth.get_transaction_count(self.wallet_address)
        
        tx = self.contract.functions.fileReport(
            location_hash,
            incident_type,
            content_hash,
            resolution_token_hash
        ).build_transaction({
            'chainId': 11155111,
            'gas': 1500000, # Back down to normal gas limit because we removed Strings!
            'maxFeePerGas': self.web3.to_wei('2', 'gwei'),
            'maxPriorityFeePerGas': self.web3.to_wei('1', 'gwei'),
            'nonce': nonce,
        })
        
        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return self.web3.to_hex(tx_hash)

    def mark_resolved_on_chain(self, report_id: int, secret_phrase: str) -> str:
        nonce = self.web3.eth.get_transaction_count(self.wallet_address)
        
        tx = self.contract.functions.markResolved(
            report_id,
            secret_phrase
        ).build_transaction({
            'chainId': 11155111,
            'gas': 1000000,
            'maxFeePerGas': self.web3.to_wei('2', 'gwei'),
            'maxPriorityFeePerGas': self.web3.to_wei('1', 'gwei'),
            'nonce': nonce,
        })
        
        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return self.web3.to_hex(tx_hash)
