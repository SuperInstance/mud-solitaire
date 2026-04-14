#!/usr/bin/env python3
"""HTTP-to-MUD Bridge — agents connect via REST API.

Endpoints:
  POST /mud/connect  {"name":"jc1","role":"vessel"}  → session token
  POST /mud/cmd      {"token":"...","cmd":"look"}     → MUD response
  GET  /mud/state    ?token=...                        → current room state
  GET  /mud/who                                       → who's online
  POST /mud/disconnect {"token":"..."}                 → disconnect

Agents use this to join the MUD, navigate rooms, and coordinate.
"""
import json, socket, threading, time, uuid, http.server, socketserver
from urllib.parse import urlparse, parse_qs

MUD_HOST = "127.0.0.1"
MUD_PORT = 7777
API_PORT = 8902

sessions = {}  # token -> {name, role, socket, buffer}

def mud_connect(name, role="agent"):
    """Connect to the MUD server, login, return (socket, welcome)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((MUD_HOST, MUD_PORT))
    
    # Read welcome + name prompt
    welcome = s.recv(4096).decode(errors='replace')
    # Read role prompt
    welcome += s.recv(4096).decode(errors='replace')
    
    # Send name
    s.sendall((name + "\n").encode())
    time.sleep(0.3)
    resp = s.recv(4096).decode(errors='replace')
    
    # Send role
    s.sendall((role + "\n").encode())
    time.sleep(0.3)
    resp += s.recv(4096).decode(errors='replace')
    
    s.setblocking(False)
    return s, welcome + resp

def mud_cmd(sock, cmd):
    """Send a command to MUD, return response."""
    try:
        # Drain any pending data
        try: sock.recv(8192)
        except: pass
        sock.sendall((cmd + "\n").encode())
        time.sleep(0.5)
        chunks = []
        try:
            while True:
                chunk = sock.recv(4096).decode(errors='replace')
                if not chunk: break
                chunks.append(chunk)
                time.sleep(0.1)
        except: pass
        return "".join(chunks)
    except Exception as e:
        return f"Error: {e}"

class MudAPIHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if parsed.path == "/mud/who":
            names = [s["name"] for s in sessions.values()]
            self.send_json({"online": names, "count": len(names)})
        
        elif parsed.path == "/mud/state":
            token = params.get("token", [None])[0]
            if token and token in sessions:
                resp = mud_cmd(sessions[token]["socket"], "look")
                self.send_json({"room": resp, "agent": sessions[token]["name"]})
            else:
                self.send_json({"error": "invalid token"}, 401)
        
        elif parsed.path == "/":
            self.send_json({"service": "mud-bridge", "mud_port": MUD_PORT, "agents_online": len(sessions),
                          "endpoints": ["/mud/connect", "/mud/cmd", "/mud/state", "/mud/who", "/mud/disconnect"]})
        
        else:
            self.send_json({"error": "not found"}, 404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        body = self.read_json()
        
        if parsed.path == "/mud/connect":
            name = body.get("name", f"agent-{uuid.uuid4().hex[:6]}")
            role = body.get("role", "agent")
            try:
                sock, welcome = mud_connect(name, role)
                token = uuid.uuid4().hex
                sessions[token] = {"name": name, "role": role, "socket": sock, "connected": time.time()}
                self.send_json({"token": token, "name": name, "welcome": welcome[:500], "status": "connected"})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        
        elif parsed.path == "/mud/cmd":
            token = body.get("token")
            cmd = body.get("cmd", "look")
            if token and token in sessions:
                resp = mud_cmd(sessions[token]["socket"], cmd)
                self.send_json({"response": resp, "agent": sessions[token]["name"]})
            else:
                self.send_json({"error": "invalid token"}, 401)
        
        elif parsed.path == "/mud/disconnect":
            token = body.get("token")
            if token and token in sessions:
                try: sessions[token]["socket"].close()
                except: pass
                name = sessions[token]["name"]
                del sessions[token]
                self.send_json({"status": "disconnected", "name": name})
            else:
                self.send_json({"error": "invalid token"}, 401)
        
        else:
            self.send_json({"error": "not found"}, 404)
    
    def read_json(self):
        length = int(self.headers.get('Content-Length', 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}
    
    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, *a):
        print(f"[MUD-API] {a[0]}")

if __name__ == "__main__":
    print(f"MUD→HTTP Bridge on :{API_PORT}")
    print(f"Connecting to MUD at {MUD_HOST}:{MUD_PORT}")
    with socketserver.TCPServer(("", API_PORT), MudAPIHandler) as httpd:
        httpd.serve_forever()
