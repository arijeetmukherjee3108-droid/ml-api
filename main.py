from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel

# Import our strictly separated modules
import blockchain_module
import ml_data_module

app = FastAPI(title="SafeHer API")

INCIDENT_MAP = {
    "Harassment": 0,
    "Stalking": 1,
    "Suspicious": 2,
    "Other": 3
}

class ResolveReportRequest(BaseModel):
    report_id: int
    secret: str

@app.post("/api/reports/submit")
async def submit_report(
    lat: float = Form(...),
    lng: float = Form(...),
    incident_type: str = Form(...),
    description: str = Form(""),
    suspect_name: str = Form(""),
    evidence_file: UploadFile = File(...)
):
    """
    CLEAN ORCHESTRATOR:
    This endpoint coordinates between the Blockchain and the ML Data modules.
    """
    
    # 1. Step into the 'Blockchain Backend' territory
    # This handles Pinata, Hashing, and Ethereum.
    try:
        file_content = await evidence_file.read()
        blockchain_result = await blockchain_module.submit_to_blockchain_layer(
            lat=lat,
            lng=lng,
            mapped_type=INCIDENT_MAP.get(incident_type, 3),
            suspect_name=suspect_name,
            description=description,
            evidence_file_name=evidence_file.filename,
            evidence_file_content=file_content
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain Layer Error: {str(e)}")

    # 2. Step into the 'ML Data Backend' territory
    # This saves the raw metrics for the predictive heatmap model.
    ml_data_module.save_raw_data_for_ml(
        lat=lat,
        lng=lng,
        incident_type=incident_type,
        description=description,
        suspect_name=suspect_name,
        evidence_url=blockchain_result["ipfs_url"],
        ipfs_cid=blockchain_result["ipfs_cid"]
    )

    # 3. Return the combined response
    return {
        "status": "success",
        "blockchain_receipt": blockchain_result["blockchain_receipt"],
        "ipfs_url": blockchain_result["ipfs_url"],
        "resolution_secret": blockchain_result["resolution_secret"],
        "message": "Report successfully filed on-chain and cached for ML mapping."
    }

@app.post("/api/reports/resolve")
async def resolve_report(request: ResolveReportRequest):
    """
    Blockchain-specific endpoint to resolve a report.
    """
    try:
        receipt_url = blockchain_module.resolve_on_chain(request.report_id, request.secret)
        return {
            "status": "success",
            "message": "Report permanently marked as Resolved on Web3.",
            "blockchain_receipt": receipt_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain resolution failed: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "SafeHer Unified Backend: Modular Architecture Online"}
