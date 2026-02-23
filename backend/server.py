from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import subprocess
import threading

app = FastAPI()

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserConfig(BaseModel):
    groq_api_key: str
    linkedin_email: str
    linkedin_password: str
    cv_path: str
    salary_expectation: int
    location: str
    commuting: str
    veteran_status: str
    disability: str
    ethnicity: str
    gender: str
    address: str
    zip_code: str
    middle_name: str
    phone: str

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app-groq.py'))

def run_script():
    try:
        # Run the automation script as a subprocess
        print(f"Starting automation script: {SCRIPT_PATH}")
        subprocess.run(["python", SCRIPT_PATH], check=True)
        print("Automation script finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running automation script: {e}")
    except Exception as e:
         print(f"Unexpected error: {e}")

@app.post("/api/start")
async def start_automation(config: UserConfig, background_tasks: BackgroundTasks):
    try:
        # Write config to JSON file
        config_dict = config.dict()
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(config_dict, f, indent=4)
        
        # Start script in background
        background_tasks.add_task(run_script)
        
        return {"status": "success", "message": "Automation started in the background."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    # Basic status check
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
