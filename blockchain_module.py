import os
import secrets
import requests
from web3 import Web3
from web3_service import Web3Service

# Pinata API Config
PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_API_SECRET = os.getenv("PINATA_API_SECRET")
PINATA_BASE_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"

# Initialize the low-level blockchain bridge
blockchain_service = Web3Service()

def upload_to_pinata(file_name: str, file_content: bytes) -> str:
    """
    Securely uploads a file to IPFS via Pinata.
    Returns the IPFS CID (Hash).
    """
    if not PINATA_API_KEY or not PINATA_API_SECRET:
        raise Exception("Pinata API credentials missing in .env")

    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_API_SECRET
    }
    
    files = {
        'file': (file_name, file_content)
    }
    
    response = requests.post(PINATA_BASE_URL, files=files, headers=headers)
    
    if response.status_code == 200:
        return response.json()["IpfsHash"]
    else:
        raise Exception(f"Pinata Upload Failed: {response.text}")

async def submit_to_blockchain_layer(
    lat: float, 
    lng: float, 
    mapped_type: int, 
    suspect_name: str, 
    description: str,
    evidence_file_name: str,
    evidence_file_content: bytes
):
    """
    Handles decentralized storage (IPFS) and Blockchain anchoring.
    This is the core 'Blockchain Backend' logic.
    """
    
    # 1. Upload file to Pinata IPFS
    ipfs_cid = upload_to_pinata(evidence_file_name, evidence_file_content)
    ipfs_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_cid}"

    # 2. Generate the Anonymous Resolution Secret
    generated_secret = secrets.token_hex(16)
    resolution_token_hash = Web3.keccak(text=generated_secret)

    # 3. Generate the Content Hash for Blockchain Integrity (Anchor: Suspect Name + IPFS CID)
    # This prevents anyone from tampering with the suspect name or image later.
    content_payload = f"{suspect_name}|{ipfs_cid}"
    content_hash = Web3.keccak(text=content_payload)

    # 4. Push hashes to Ethereum Sepolia Testnet
    tx_hash = blockchain_service.file_report_on_chain(
        lat, 
        lng, 
        mapped_type,
        content_hash,
        resolution_token_hash
    )
    
    etherscan_url = f"https://sepolia.etherscan.io/tx/{tx_hash}"

    return {
        "blockchain_receipt": etherscan_url,
        "ipfs_url": ipfs_url,
        "ipfs_cid": ipfs_cid,
        "resolution_secret": generated_secret
    }

def resolve_on_chain(report_id: int, secret_phrase: str):
    """
    Marks a report resolved on the blockchain using the anonymous secret.
    """
    tx_hash = blockchain_service.mark_resolved_on_chain(report_id, secret_phrase)
    return f"https://sepolia.etherscan.io/tx/{tx_hash}"
