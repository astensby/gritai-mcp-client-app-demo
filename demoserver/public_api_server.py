import logging
import requests
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("police-incidents", dependencies=["requests"])

def get_latest_incidents() -> str:
    """Fetch the latest incidents from the Politiet API"""
    url = 'https://api.politiloggen.politiet.no/messages'
    headers = {'accept': 'text/plain'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.text
    except requests.exceptions.Timeout:
        error_msg = "Request timed out while fetching incidents"
        logger.error(error_msg)
        return error_msg
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching incidents: {e}")
        return "Unable to fetch incidents at this time. Please try again later."

def get_incidents_by_municipality(municipality: str) -> str:
    """Fetch incidents for a specific municipality from the Politiet API
    
    Args:
        municipality: The municipality name to search for (e.g., "Oslo", "Bergen")
    """
    if not municipality or not municipality.strip():
        return "Error: Municipality name cannot be empty."
    
    url = 'https://api.politiloggen.politiet.no/messages'
    headers = {'accept': 'text/plain'}
    params = {'Municipalities': municipality.strip()}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.text
    except requests.exceptions.Timeout:
        error_msg = f"Request timed out while fetching incidents for {municipality}"
        logger.error(error_msg)
        return f"Unable to fetch incidents for {municipality} at this time. Please try again later."
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching incidents for {municipality}: {e}")
        return f"Unable to fetch incidents for {municipality} at this time. Please try again later."

@mcp.tool()
def latest_incidents() -> str:
    """Get the 10 latest police incidents"""
    incidents = get_latest_incidents()
    return incidents

@mcp.tool()
def incidents_by_municipality(municipality: str) -> str:
    """Get the latest police incidents for a specific municipality.
    
    Args:
        municipality: The municipality to fetch incidents for.
    """
    incidents = get_incidents_by_municipality(municipality)
    return incidents

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')

