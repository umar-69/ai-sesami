from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Read the request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else b""
        response = {"error": "No query provided."}
        status = 400

        try:
            if body:
                data = json.loads(body)
                user_query = data.get("query", "")
            else:
                user_query = ""

            if user_query:
                # For demonstration purposes, we'll use a placeholder response
                # In a real implementation, you would call the Sesame AI API directly
                ai_reply_text = f"You said: {user_query}. This is a response from the Sesame AI voice assistant."
                
                # Structure the response
                response = {"reply": ai_reply_text}
                status = 200
            else:
                response = {"error": "Query is empty."}
                status = 400
        except Exception as e:
            response = {"error": str(e)}
            status = 500

        # Send HTTP response
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS for local development
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        # Handle preflight requests for CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 