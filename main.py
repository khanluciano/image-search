import os
import sys
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic_settings import BaseSettings, SettingsConfigDict

# ─── ENVIRONMENT CONFIGURATION & VALIDATION ───
class Settings(BaseSettings):
    # This enforces that SERPAPI_TOKEN must be a non-empty string in your .env file
    SERPAPI_TOKEN: str
         
    # Instructs Pydantic to read from a file named '.env' automatically
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

try:
    settings = Settings()
    print("\n✅ [SUCCESS] Environment variables validated. SERPAPI_TOKEN is loaded.\n")
except Exception as e:
    print("\n" + "="*60)
    print("❌ [CRITICAL ERROR] Environment Validation Failed!")
    print(f"Details: {e}")
    print("\n👉 ACTION REQUIRED:")
    print("1. Ensure a file named exactly '.env' exists in this directory.")
    print("2. Ensure it contains: SERPAPI_TOKEN=your_actual_key_here")
    print("="*60 + "\n")
    sys.exit(1)

# ─── FASTAPI INSTANTIATION ───
app = FastAPI(title="Global Image Matcher Dashboard")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def load_homepage(request: Request):
    """Serves the main application dashboard layout."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/search-free-lens")
async def run_free_lens_lookup(file: UploadFile = File(...)):
    """
    Implements SerpApi's official two-step Google Lens pipeline.
    Step 1: POST binary bytes to /image to get an image_id.
    Step 2: GET search results from /search using that image_id.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, 
            detail="Invalid Document: Upload must be a valid image format."
        )

    try:
        image_binary = await file.read()
                 
        # ─── STEP 1: UPLOAD IMAGE TO GET AN IMAGE_ID (POST) ───
        print(f"Step 1: Uploading '{file.filename}' to SerpApi Image Manager...")
                 
        # According to documentation, endpoint is https://serpapi.com/image
        upload_url = "https://serpapi.com/image"
        
        # Form field parameters for multipart data
        payload = {"api_key": settings.SERPAPI_TOKEN}
        multipart_data = {
            'image': (str(file.filename), image_binary, str(file.content_type))
        }
                 
        upload_response = requests.post(
            upload_url, 
            data=payload, 
            files=multipart_data, 
            timeout=30
        )
                 
        if upload_response.status_code != 200:
            print(f"Upload Failure Raw Body: {upload_response.text}")
            raise HTTPException(
                status_code=upload_response.status_code, 
                detail="Image Upload Step Failed: Check terminal log output."
            )
                     
        upload_data = upload_response.json()
        image_id = upload_data.get("image_id")
                 
        if not image_id:
            raise HTTPException(
                status_code=500, 
                detail="SerpApi uploaded the file but failed to return an image_id."
            )
                     
        # ─── STEP 2: SEARCH GOOGLE LENS USING THE IMAGE_ID (GET) ───
        print(f"Step 2: Processing URL search parameters for image_id: {image_id}...")
                 
        # Engine routing happens at the main /search route via parameters
        search_url = "https://serpapi.com/search"
                 
        search_params = {
            "engine": "google_lens",
            "api_key": settings.SERPAPI_TOKEN,
            "image_id": image_id
        }
                 
        search_transaction = requests.get(search_url, params=search_params, timeout=35)
                 
        if search_transaction.status_code != 200:
            print(f"Search Failure Raw Body response: {search_transaction.text}")
            if search_transaction.status_code == 401:
                raise HTTPException(
                    status_code=401, 
                    detail="SerpApi Error: Key is invalid or free limits expired."
                )
            raise HTTPException(
                status_code=search_transaction.status_code, 
                detail=f"Engine Search Step Failed with status {search_transaction.status_code}. Check terminal console."
            )

        json_payload = search_transaction.json()
        visual_records = json_payload.get("visual_matches", [])
                 
        transformed_output = []
        for record in visual_records:
            transformed_output.append({
                "title": record.get("title", "Matched Profile Image Link"),
                "source_domain": record.get("source", "Unknown Domain Website"),
                "profile_url": record.get("link", "#"),
                "thumbnail": record.get("thumbnail", "https://placeholder.com")
            })

        return {"matches": transformed_output[:15]}

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="The connection to SerpApi timed out.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Verify that your computer is connected to the internet.")
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Parser Exception: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    # Passing as a string ("main:app") is mandatory when reload=True is active
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
