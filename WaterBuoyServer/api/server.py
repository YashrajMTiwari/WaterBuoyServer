from sanic import Sanic
from sanic.response import json
from supabase import create_client, Client
import os
import logging

# Initialize logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = Sanic("DeviceLocationService")

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://yakviserjdksmpqvnumd.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlha3Zpc2VyamRrc21wcXZudW1kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU3OTcwMDksImV4cCI6MjA1MTM3MzAwOX0.UreNwiGY46qn51FcSQno-IOpYLtj3q0eRX56OqYy6H4")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.post("/location")
async def update_location(request):
    data = request.json
    device_id = data.get("device_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not all([device_id, latitude, longitude]):
        return json({"error": "Missing required fields"}, status=400)

    try:
        # Specify the conflict target to handle conflicts by 'device_id'
        response_data = supabase.table("device_location").upsert({
            "device_id": device_id,
            "latitude": latitude,
            "longitude": longitude
        }, on_conflict=["device_id"]).execute()

        # Check if the operation was successful
        if response_data.data:
            return json({"message": "Location data updated successfully"}, status=200)
        elif response_data.error:
            logger.error(f"Upsert failed: {response_data.error}")
            return json({"error": "Failed to update location data"}, status=500)
        else:
            logger.error(f"Unexpected response: {response_data}")
            return json({"error": "Unexpected error occurred"}, status=500)

    except Exception as e:
        logger.error(f"Error in updating location: {str(e)}")
        return json({"error": "An unexpected error occurred", "details": str(e)}, status=500)


@app.get("/location/<device_id>")
async def get_location(request, device_id):
    try:
        response_data = supabase.table("device_location").select("device_id, latitude, longitude").eq("device_id", device_id).limit(1).execute()

        if response_data.data:
            return json(response_data.data[0], status=200)
        else:
            return json({"error": "Device not found"}, status=404)

    except Exception as e:
        logger.error(f"Error in fetching location: {str(e)}")
        return json({"error": "An unexpected error occurred", "details": str(e)}, status=500)


@app.middleware("response")
async def add_cors_headers(request, response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, access_log=True)
