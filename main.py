import os
import random
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any

from database import db, create_document, get_documents
from schemas import Incident

app = FastAPI(title="Police Smart Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Police Smart Analytics Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ========== Analytics Endpoints ==========

class IncidentIn(Incident):
    pass


@app.post("/incidents")
def create_incident(payload: IncidentIn):
    try:
        inserted_id = create_document("incident", payload)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidents")
def list_incidents(
    type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    precinct: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    try:
        filters: Dict[str, Any] = {}
        if type: filters["type"] = type
        if severity: filters["severity"] = severity
        if status: filters["status"] = status
        if precinct: filters["precinct"] = precinct
        docs = get_documents("incident", filters, limit)
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        # Sort newest first if timestamps present
        docs.sort(key=lambda x: x.get("reported_at", ""), reverse=True)
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/summary")
def analytics_summary(
    precinct: Optional[str] = None,
    period: Optional[str] = Query("7d", description="Time window like 24h,7d,30d"),
):
    try:
        # Basic aggregation in Python; for large data, use Mongo aggregations
        filters: Dict[str, Any] = {}
        if precinct:
            filters["precinct"] = precinct
        docs = get_documents("incident", filters, None)

        total = len(docs)
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        open_cases = 0
        avg_response = None
        response_sum = 0.0
        response_count = 0

        for d in docs:
            t = d.get("type", "other")
            by_type[t] = by_type.get(t, 0) + 1
            s = d.get("severity", "medium")
            by_severity[s] = by_severity.get(s, 0) + 1
            if d.get("status") in {"reported", "dispatched", "on_scene"}:
                open_cases += 1
            if d.get("response_minutes") is not None:
                response_sum += float(d["response_minutes"])  # type: ignore
                response_count += 1

        if response_count:
            avg_response = round(response_sum / response_count, 2)

        return {
            "total": total,
            "open": open_cases,
            "avg_response_minutes": avg_response,
            "by_type": by_type,
            "by_severity": by_severity,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/incidents/seed")
def seed_incidents(n: int = Query(50, ge=1, le=500)):
    """Create random sample incidents for demo purposes"""
    try:
        types = [
            "theft",
            "assault",
            "burglary",
            "fraud",
            "vandalism",
            "traffic",
            "narcotics",
            "disturbance",
            "other",
        ]
        severities = ["low", "medium", "high", "critical"]
        statuses = ["reported", "dispatched", "on_scene", "resolved", "closed"]
        precincts = ["Central", "North", "South", "East", "West"]

        # Rough bounding box (San Francisco area as example)
        lat_min, lat_max = 37.70, 37.82
        lon_min, lon_max = -122.52, -122.36

        created = 0
        now = datetime.now(timezone.utc)
        for i in range(n):
            t = random.choice(types)
            sev = random.choices(severities, weights=[4, 6, 3, 1])[0]
            status = random.choices(statuses, weights=[3, 3, 2, 2, 2])[0]
            when = now - timedelta(minutes=random.randint(10, 60 * 24 * 14))
            report_when = when + timedelta(minutes=random.randint(0, 120))
            response_minutes = random.randint(2, 60) if status != "reported" else None
            doc = Incident(
                incident_id=f"INC-{random.randint(100000, 999999)}",
                type=t,
                description=f"Random {t} incident",
                severity=sev,  # type: ignore
                status=status,  # type: ignore
                latitude=round(random.uniform(lat_min, lat_max), 6),
                longitude=round(random.uniform(lon_min, lon_max), 6),
                occurred_at=when.isoformat(),
                reported_at=report_when.isoformat(),
                response_minutes=response_minutes,  # type: ignore
                precinct=random.choice(precincts),
                officer_id=str(random.randint(1000, 9999)),
            )
            create_document("incident", doc)
            created += 1
        return {"created": created}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
