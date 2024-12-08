import http.server
import socketserver
import webbrowser
from urllib.parse import urlparse, parse_qs
import threading
import queue

import http.server
import socketserver
import webbrowser
from urllib.parse import urlparse, parse_qs
import threading
import queue

class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, auth_code_queue, *args, **kwargs):
        self.auth_code_queue = auth_code_queue
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle the callback from Spotify"""
        query_components = parse_qs(urlparse(self.path).query)
        
        # Send a response to the browser
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if 'code' in query_components:
            auth_code = query_components['code'][0]
            self.auth_code_queue.put(auth_code)
            response = """
            <html><body>
            <h1>Authorization Successful!</h1>
            <p>You can close this window and return to the application.</p>
            </body></html>
            """
        else:
            response = """
            <html><body>
            <h1>Authorization Failed!</h1>
            <p>No authorization code received.</p>
            </body></html>
            """
            
        self.wfile.write(response.encode('utf-8'))

def get_spotify_auth_code(client_id):
    """Start local server and get authorization code"""
    PORT = 8888
    auth_code_queue = queue.Queue()
    
    # Create handler with access to the queue
    handler = lambda *args, **kwargs: OAuthHandler(auth_code_queue, *args, **kwargs)
    
    # Start server in a separate thread
    server = socketserver.TCPServer(("", PORT), handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Construct and open the authorization URL
    redirect_uri = f"http://localhost:{PORT}/callback"
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={client_id}"
        "&response_type=code"
        f"&redirect_uri={redirect_uri}"
        "&scope=user-library-read user-read-private user-read-email "
        "user-read-playback-state user-read-currently-playing playlist-read-private"
    )
    
    webbrowser.open(auth_url)
    
    try:
        # Wait for the authorization code
        auth_code = auth_code_queue.get(timeout=300)  # 5 minute timeout
        return auth_code, redirect_uri
    finally:
        server.shutdown()
        server.server_close()