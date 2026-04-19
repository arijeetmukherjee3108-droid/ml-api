# SafeHer Blockchain Integration Guide

This directory contains the necessary components for logging incident reports to the Ethereum Sepolia Testnet, fulfilling the "Blockchain Integrity" pillar of the SafeHer Hackathon Project Proposal.

## Architecture & Data Flow
When a user submits an incident report via the Android application, here is how the data flows across your layers:

```
[ FRONTEND ]                  [ BACKEND ]                       [ BLOCKCHAIN ]
Android Kotlin     ======>   FastAPI (Python)      ======>     Ethereum Sepolia
(Retrofit POST)              (Web3.py script)                  (SafetyReports.sol)
```

1. **Frontend (Android):** The user clicks "Submit Incident", grabbing their GPS coordinates, an incident category (like "harassment"), and triggering an API call.
2. **Backend (FastAPI):** Your Python server receives the request.
   - It saves the detailed report (including an optional photo/description) natively to Firebase Firestore so standard app functions and the ML model can use it.
   - It hashes the raw location and sends just the location hash, incident type, and timestamp to the Blockchain via `web3_service.py`. 
3. **Blockchain (Ethereum):** The Ethereum node processes the transaction, modifying the state on the Sepolia test network and emitting a public transaction hash.
4. **Conclusion:** FastAPI returns that transaction hash immediately to Retrofit. Android displays the verifiable URL `https://sepolia.etherscan.io/tx/{HASH}` to the user.

---

## 1. Blockchain Setup (Deploying the Smart Contract)
You need to deploy the Solidity contract provided in `contracts/SafetyReports.sol` to the network.

1. Install the MetaMask extension in your browser. Create a wallet and set it to **Sepolia Test Network**.
2. Go to a Sepolia Faucet (like [Alchemy Faucet](https://sepoliafaucet.com/)) and get free test ETH.
3. Open [Remix IDE](https://remix.ethereum.org/).
4. Create a file inside Remix called `SafetyReports.sol` and paste the code from `contracts/SafetyReports.sol`.
5. Compile the contract using the compiler tab.
6. Open the **Deploy & Run Transactions** tab. Change Environment to **Injected Provider - MetaMask**. 
7. Click **Deploy**. Approve the prompt in MetaMask.
8. Locate your Deployed Contract in Remix. You MUST copy two things:
   - The **Contract Address**.
   - The **Contract ABI** (From the compiler tab). (Note: We have pre-filled the ABI inside `backend_utils/web3_service.py` to save you time. If you alter the `.sol` file, you need to update the ABI!).

---

## 2. Backend Setup (FastAPI + Web3.py)
This is where the magic happens behind the scenes. The Android frontend does *not* talk directly to the blockchain. FastApi does it for them to save the user from needing a crypto wallet on their phone.

1. Ensure the backend has `web3` and `python-dotenv` installed: `pip install web3 python-dotenv`
2. Create an account on Alchemy or Infura to get a free **Sepolia RPC URL** (this is an API endpoint like `https://eth-sepolia.g.alchemy.com/v2/your_key`).
3. Set your `.env` variables inside your FastAPI environment:
   ```env
   SEPOLIA_RPC_URL="https://eth-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_KEY"
   METAMASK_PUBLIC_ADDRESS="0xYourMetaMaskAddress"
   METAMASK_PRIVATE_KEY="YourMetaMaskPrivateKey"
   CONTRACT_ADDRESS="0xAddressOfYourDeployedContract"
   ```
4. Now, in your FastAPI `main.py`, you can import and use the service provided in `backend_utils/web3_service.py`:

```python
from fastapi import FastAPI
# Assuming you move web3_service.py appropriately within your backend package:
from .web3_service import Web3Service

app = FastAPI()
blockchain_service = Web3Service()

@app.post("/api/reports/submit")
async def submit_report(lat: float, lng: float, incident_type: str):
    # 1. First, save everything to Firebase Firestore (detailed data)
    # firebase_db.collection('reports').add(...)

    # 2. Add an immutable footprint on the Ethereum Blockchain
    tx_hash = blockchain_service.file_report_on_chain(lat, lng, incident_type)
    
    # 3. Return the transaction URL to Android!
    etherscan_url = f"https://sepolia.etherscan.io/tx/{tx_hash}"
    
    return {
        "status": "success",
        "blockchain_receipt": etherscan_url
    }
```

---

## 3. Frontend Setup (Android Retrofit)

On the Android Frontend, your Retrofit API interface will look something like this:

```kotlin
data class SubmitReportRequest(
    val lat: Double,
    val lng: Double,
    val incident_type: String
)

data class SubmitReportResponse(
    val status: String,
    val blockchain_receipt: String
)

interface SafeHerApi {
    @POST("/api/reports/submit")
    suspend fun submitIncidentReport(@Body request: SubmitReportRequest): Response<SubmitReportResponse>
}
```

When you receive the `blockchain_receipt` String URL in the response, display it to the user. E.g., make it a clickable TextView that opens their phone's browser to prove that their data cannot be altered or removed!
