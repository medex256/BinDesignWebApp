import socketio

# Create a Socket.IO client
io = socketio.Client()

@io.event
def connect():
    print("Connection established")

@io.event
def disconnect():
    print("Disconnected from server")

@io.event
def message(data):
    print(f"Message from server: {data}")

@io.event
def connect_error(data):
    print(f"Connection failed: {data}")

@io.event
def error(data):
    print(f"Error from server: {data}")

headers = {
     'bin_id': '1'
}
auth = {
    'username':'password'
}

try:
    io.connect('http://localhost:5000', headers=headers, auth=auth, transports=['websocket'])

    while True:
        pass
    
except Exception as e:
    print(f"Failed to connect to the server: {e}")