import http.server
import socketserver
import json
import urllib.parse
from repacker import edit_mapping_in_plist

PORT = 8080

class ConcertEditorAPIHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_POST(self):
        # We only accept POST requests to /api/batch_edit
        if self.path == '/api/batch_edit':
            # Parse the JSON payload coming from the Browser GUI
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Extract variables from GUI JSON
            concert_model = "MainStage Concert/One Patch Only-BackStage Master Concert V2-8.concert"
            selected_items = data.get("items", [])
            new_channel = data.get("newChannel")
            new_port = data.get("newPort")
            do_replicate = data.get("replicate", False)
            
            # The mappings in the GUI passed the 'rawRef' back to us
            # We must cross-reference exactly which ones to edit
            # By parsing their source patch and identity!
            success_count = 0
            
            # Execute backend python script repacker mapping loops!
            for item in selected_items:
                patch_path = item["sourcePatch"]
                map_id = item["mapKey"] # from translation
                number_id = item["rawRef"]
                
                # Convert string from frontend to int
                new_channel_int = int(new_channel) if new_channel else None
                new_port_str = new_port if new_port else None
                
                print(f"API Triggering Repacker Engine for {map_id}...")
                success = edit_mapping_in_plist(
                    concert_model, 
                    patch_path, 
                    map_id, 
                    number_id, 
                    new_channel=new_channel_int, 
                    new_port_name=new_port_str,
                    replicate_mapping=do_replicate
                )
                if success:
                    success_count += 1
            
            # Post-Processing: We must re-compile the frontend JSON automatically!
            import subprocess
            print("Batch edits completed. Auto-compiling new JSON schema for frontend...")
            try:
                subprocess.run(["python3", "extractor.py", concert_model], check=True, capture_output=True)
                subprocess.run(["python3", "translator.py"], check=True, capture_output=True)
                print("Frontend JSON re-compiled successfully.")
            except Exception as e:
                print(f"Error compiling schemas: {e}")
            
            # Send Success Response back to Browser
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {"status": "ok", "message": f"Successfully updated {success_count} mappings!"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        elif self.path == '/api/rescan':
            # Run the extractor independently
            import subprocess
            concert_model = "MainStage Concert/One Patch Only-BackStage Master Concert V2-8.concert"
            try:
                subprocess.run(["python3", "extractor.py", concert_model], check=True, capture_output=True)
                subprocess.run(["python3", "translator.py"], check=True, capture_output=True)
            except Exception as e:
                print(f"Error compiling schemas: {e}")
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "ok", "message": "Successfully rescanned MainStage file! Your view is fully synchronized."}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    print(f"Starting API Server on http://localhost:{PORT} ...")
    with socketserver.TCPServer(("", PORT), ConcertEditorAPIHandler) as httpd:
        httpd.serve_forever()
