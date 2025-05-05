from http.server import BaseHTTPRequestHandler
import json
from sesame_ai import SesameAI, TokenManager, APIError, NetworkError

# Initialize outside the handler for potential reuse (may not persist in all serverless environments)
# Consider implications if state is not maintained across invocations
try:
    api_client = SesameAI()
    # Using a temporary file path; Vercel might require /tmp/
    # Adjust token_file path if needed for persistent storage (e.g., external DB/cache)
    token_manager = TokenManager(api_client, token_file="/tmp/token.json")
except Exception as e:
    # Handle potential init errors
    api_client = None
    token_manager = None
    print(f"Error initializing SesameAI: {e}")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):  # Changed to GET for simplicity, can be POST
        response = {}
        status = 500

        if not token_manager:
            response = {"error": "SesameAI client not initialized."}
            status = 503 # Service Unavailable
        else:
            try:
                # Get a valid token (creates account/refreshes automatically)
                id_token = token_manager.get_valid_token()
                response = {"id_token": id_token}
                status = 200
            except (APIError, NetworkError) as e:
                response = {"error": f"SesameAI authentication error: {e}"}
                status = 502 # Bad Gateway
            except Exception as e:
                response = {"error": f"An unexpected error occurred: {str(e)}"}
                status = 500

        # Send HTTP response
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS') # Added GET
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    # Keep OPTIONS for CORS preflight
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS') # Added GET
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

# Remove the old do_POST method entirely if only GET is needed for auth
# If POST is preferred, adapt the do_GET logic into do_POST 