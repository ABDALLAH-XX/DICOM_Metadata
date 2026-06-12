import os
from pathlib import Path
import pydicom
import pandas as pd
import sqlite3

# 1. Path Configuration
# Set the absolute path to the directory containing your DICOM files
DICOM_DIR = Path("/home/abdallah/Bureau/DICOM_Metadata/dicom-backend/vhm_head") 
DB_PATH = "crane_metadata.db"

metadata_list = []

print("Extracting DICOM metadata...")

# 2. Iterate through all files in the directory
# Filter to process files only, ignoring hidden subdirectories
for file_path in DICOM_DIR.iterdir():
    if file_path.is_file():
        try:
            # Read header metadata only (ignores heavy pixel arrays for maximum speed)
            ds = pydicom.dcmread(file_path, stop_before_pixels=True)
            
            # Safe tag extraction with fallbacks
            patient_id = ds.PatientID if 'PatientID' in ds else "Anonymous"
            instance_num = int(ds.InstanceNumber) if 'InstanceNumber' in ds else 0
            thickness = float(ds.SliceThickness) if 'SliceThickness' in ds else 0.0
            
            # Retrieve Z-coordinate (via ImagePositionPatient or SliceLocation)
            z_coordinate = 0.0
            if 'ImagePositionPatient' in ds:
                z_coordinate = float(ds.ImagePositionPatient[2])
            elif 'SliceLocation' in ds:
                z_coordinate = float(ds.SliceLocation)
            
            # Store extracted slice metadata into a dictionary
            metadata_list.append({
                "file_name": file_path.name,
                "absolute_path": str(file_path.resolve()),
                "patient_id": patient_id,
                "instance_number": instance_num,
                "slice_thickness": thickness,
                "slice_location_z": z_coordinate
            })
            
        except Exception as e:
            # Security fallback in case a non-DICOM file is found in the folder
            print(f"Failed to read file {file_path.name}: {e}")

# 3. Create Pandas DataFrame and apply Spatial Sorting
df = pd.DataFrame(metadata_list)

# Sort slices chronologically along the Z-axis (from head base to top)
df = df.sort_values(by="slice_location_z").reset_index(drop=True)

print(f"{len(df)} images successfully indexed and sorted! Top 5 slices:")
print(df[["instance_number", "slice_location_z"]].head())

# 4. Export to SQLite Database
conn = sqlite3.connect(DB_PATH)
# 'replace' overwrites the table properly on every run
df.to_sql("coupes_crane", conn, if_exists="replace", index=False)
conn.close()

print(f"\n Database successfully saved at: {DB_PATH}")