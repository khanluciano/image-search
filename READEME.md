### Global Image Matcher Dashboard

A FastAPI application that integrates with SerpApi's official two-step Google Lens pipeline to perform high-accuracy visual reverse image searches. 

### 🚀 Pro-Tip for Best Results

⚠️ **CRITICAL FOR ACCURACY:** For the most accurate matching results (such as identifying a specific individual), **manually crop or zoom into the person's face** using an image editor before uploading the file. Google Lens prioritizes the most prominent visual features; zooming ensures it isolates facial characteristics rather than background objects or clothing textures. 

### 🛠️ Prerequisites

* **Python 3.10+**
* A valid **SerpApi Private API Key** ([Get one here](https://serpapi.com/dashboard))

### 📦 Installation & Setup

1. **Clone or navigate** to the project directory: 

bash

cd global-image-matcher

Use code with caution.
2. **Install the required dependencies**: 

bash

pip install fastapi uvicorn requests pydantic-settings jinja2 python-multipart

3. **Create your environment configuration**:
Create a file named exactly .env in the root directory and add your SerpApi key. 

*Note: Do not include quotes or trailing spaces around your token.* 

env

SERPAPI_TOKEN=your_actual_serpapi_production_key_here


### 🎮 How to Run

1. Start the local development server: 

bash

python main.py


*(Alternatively, run uvicorn main:app --reload)*
2. Open your web browser and navigate to: 

text

http://127.0.0.1:8000

### ⚙️ Architecture Pipeline

The backend leverages a **two-step workflow** to securely handle image uploads without exposing your API credentials to the client browser: 

1. **Step 1 (Binary Upload)**: The script streams your local file via a multipart form data POST to https://serpapi.com/image. SerpApi validates the file and securely responds with a unique, temporary image_id.
2. **Step 2 (Engine Lookup)**: The script makes a secondary GET request to https://serpapi.com/search, passing the image_id and setting the engine parameter to google_lens.
3. **Data Transformation**: The API parses the raw visual_matches JSON array and transforms it into a clean, uniform payload containing the top 15 results (title, source domain, profile URL, and thumbnail preview).