from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import pydicom
from fastapi.responses import StreamingResponse
import io
from PIL import Image
import numpy as np

app = FastAPI(
    title="Mini-PACS API",
    description="API for managing and querying cranial DICOM metadata",
    version="1.0.0"
)

# CRITICAL for allowing the React frontend (usually on port 5173 or 3000)
# to communicate with FastAPI (on port 8000) without CORS security blocks.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "crane_metadata.db"

def get_db_connection():
    """Creates a connection to the SQLite database and returns rows as dictionaries."""
    conn = sqlite3.connect(DB_PATH)
    # Allows fetching rows as key-value pairs (dictionaries) instead of plain tuples.
    # This maps perfectly to JSON formats required by React.
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def home():
    return {"message": "Welcome to the Mini-PACS API. Use /api/slices to fetch data."}

@app.get("/api/slices")
def get_all_slices():
    """Returns the complete list of 245 slices sorted by anatomical Z position."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetching relevant columns for the frontend visualization list
        cursor.execute("""
            SELECT file_name, instance_number, slice_thickness, slice_location_z 
            FROM coupes_crane 
            ORDER BY slice_location_z ASC
        """)
        
        slices = cursor.fetchall()
        conn.close()
        
        # Convert SQLite row objects into standard Python dictionaries
        return [dict(row) for row in slices]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.get("/api/slices/{instance_number}/image")
def get_slice_image(instance_number: int):
    """Finds the DICOM file matching the instance number, extracts pixels, and streams a PNG."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Look up the absolute file path using the instance number
        cursor.execute("SELECT absolute_path FROM coupes_crane WHERE instance_number = ?", (instance_number,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Slice not found")
            
        file_path = row["absolute_path"]
        
        # 2. Read the full DICOM file (loading the heavy pixel array this time)
        ds = pydicom.dcmread(file_path)
        pixels = ds.pixel_array.astype(float)
        
        # 3. Pixel normalization (Mapping raw 0-2041 scale to 0-255 grayscale standard for PNG)
        normalized_pixels = ((pixels - pixels.min()) / (pixels.max() - pixels.min()) * 255.0).astype(np.uint8)
        
        # 4. Generate PNG image directly in memory (avoids disk I/O operations for speed)
        image = Image.fromarray(normalized_pixels)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        
        # 5. Return the binary raw stream of the PNG image
        return StreamingResponse(buffer, media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing error: {str(e)}")