# Import dependencies
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime  # Import datetime
import httpx
from contextlib import asynccontextmanager
from starlette.config import Config

# Load environment variables from .env
config = Config(".env")

# Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = httpx.AsyncClient()
    yield
    await app.requests_client.aclose()

# Create the FastAPI app instance with the lifespan
app = FastAPI(lifespan=lifespan)

# Set location for templates
templates = Jinja2Templates(directory="app/view_templates")

# Handle HTTP GET request for the site root '/'
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Get the current date and time
    serverTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Pass serverTime to the template
    return templates.TemplateResponse("index.html", {"request": request, "serverTime": serverTime})

# Handle HTTP GET request for /advice
@app.get("/advice", response_class=HTMLResponse)
async def advice(request: Request):
    requests_client = request.app.requests_client
    advice_url = config("ADVICE_URL")
    
    try:
        # Fetch advice from the external API
        response = await requests_client.get(advice_url)
        response.raise_for_status()
        advice_data = response.json()
    except httpx.HTTPError as e:
        advice_data = {
            "slip": {
                "advice": f"An error occurred: {str(e)}"
            }
        }
    
    # Send the advice data to the template
    return templates.TemplateResponse("advice.html", {"request": request, "data": advice_data})

# Handle HTTP GET request for /apod
@app.get("/apod", response_class=HTMLResponse)
async def apod(request: Request):
    # Define a request_client instance
    requests_client = request.app.requests_client

    # Construct the request URL using the environment variables
    nasa_apod_url = config("NASA_APOD_URL") + config("NASA_API_KEY")

    try:
        # Connect to the NASA APOD API URL and await the response
        response = await requests_client.get(nasa_apod_url)
        response.raise_for_status()  # Raise an error for bad status codes
        apod_data = response.json()
    except httpx.HTTPError as e:
        # If there is an error, use a default message
        apod_data = {
            "title": "Error",
            "explanation": f"An error occurred: {str(e)}",
            "url": "",
            "media_type": "image"
        }

    # Send the JSON data from the response in the TemplateResponse data parameter
    return templates.TemplateResponse("apod.html", {"request": request, "data": apod_data})

# Handle HTTP GET request for /params and accept a query parameter
@app.get("/params", response_class=HTMLResponse)
async def params(request: Request, name: str | None = ""):
    return templates.TemplateResponse("params.html", {"request": request, "name": name})

# Serve static files (CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
