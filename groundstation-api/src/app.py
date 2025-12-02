import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .security import verify_hmac
from .storage import (
    init_db,
    insert_telemetry,
    get_latest_telemetry,
    insert_command,
    get_last_command_seq,
)

# Shared HMAC secret used to authenticate telemetry and command messages.
HMAC_SECRET = os.getenv("HMAC_SECRET", "changeme")


class TelemetryIn(BaseModel):
    """
    Pydantic model for telemetry messages sent by the satellite node.
    This model is also used as the response model for the latest telemetry endpoint.
    """
    timestamp: str
    satellite_id: str
    latitude_deg: float
    longitude_deg: float
    altitude_km: float
    battery_soc: float
    temperature_c: float
    health: str


class CommandIn(BaseModel):
    """
    Pydantic model for commands sent to the satellite node via the ground station.
    """
    satellite_id: str
    sequence_number: int
    command_name: str
    payload: Optional[str] = None


app = FastAPI(title="Secure SatGround Lab - Groundstation API")


@app.on_event("startup")
def on_startup() -> None:
    """
    Initialize the SQLite database when the application starts.
    """
    init_db()


@app.get("/")
def root() -> dict:
    """
    Simple health-check endpoint.
    """
    return {"status": "ok", "message": "Groundstation API running."}


@app.post("/telemetry")
async def ingest_telemetry(request: Request) -> JSONResponse:
    """
    Ingest a telemetry frame from the satellite node.

    The body must be a JSON document matching TelemetryIn.
    The request must contain a valid HMAC-SHA256 signature in the `X-Signature` header.
    """
    body = await request.body()
    sig = request.headers.get("X-Signature", "")

    if not verify_hmac(body, HMAC_SECRET, sig):
        raise HTTPException(status_code=403, detail="Invalid HMAC signature")

    try:
        data = TelemetryIn.parse_raw(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}")

    insert_telemetry(data.dict())
    return JSONResponse({"status": "ok"})


@app.get(
    "/telemetry/latest",
    response_model=TelemetryIn,
    summary="Get latest telemetry frame",
    description="Return the most recent telemetry frame stored in the database.",
)
def latest_telemetry() -> TelemetryIn:
    """
    Return the latest telemetry frame.

    If no telemetry has been stored yet, this endpoint returns HTTP 404.
    """
    row = get_latest_telemetry()
    if not row:
        raise HTTPException(status_code=404, detail="No telemetry available yet")
    # `row` is already a dict shaped like TelemetryIn, so we can return it directly.
    return TelemetryIn(**row)


@app.post("/command")
async def send_command(cmd: CommandIn) -> dict:
    """
    Accept a signed command for the satellite node.

    Replay protection is implemented via the `sequence_number` field.
    The sequence number must be strictly increasing per satellite.
    """
    last_seq = get_last_command_seq(cmd.satellite_id)
    if last_seq is not None and cmd.sequence_number <= last_seq:
        raise HTTPException(
            status_code=409,
            detail="Sequence number too old (possible replay)",
        )

    insert_command(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "satellite_id": cmd.satellite_id,
            "sequence_number": cmd.sequence_number,
            "command_name": cmd.command_name,
            "payload": cmd.payload,
        }
    )
    return {"status": "accepted", "last_sequence_number": cmd.sequence_number}