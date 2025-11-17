import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from database import create_document, get_documents, db

app = FastAPI(title="Daily Gratitude API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GratitudeIn(BaseModel):
    name: str
    items: List[str]
    mood: str | None = None

@app.get("/")
def read_root():
    return {"message": "Gratitude journal backend is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
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
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

@app.post("/gratitude")
async def add_gratitude(entry: GratitudeIn):
    if not db:
        raise HTTPException(status_code=500, detail="Database not configured")
    if not entry.items or len(entry.items) == 0:
        raise HTTPException(status_code=400, detail="Provide at least one gratitude item")

    doc = entry.model_dump()
    try:
        inserted_id = create_document("gratitude", doc)
        return {"ok": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gratitude")
async def list_gratitude(limit: int = 20):
    if not db:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        docs = get_documents("gratitude", limit=limit)
        # Convert ObjectId to string and clean fields for frontend
        cleaned = []
        for d in docs:
            d["id"] = str(d.pop("_id")) if "_id" in d else None
            cleaned.append(d)
        # Reverse so newest first if timestamps exist
        cleaned.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return cleaned
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
