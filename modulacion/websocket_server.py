from flask import Flask
from flask_socketio import SocketIO, emit

# Crear la aplicación Flask y el servidor SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return  """
        <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>WebSocket en Flask</title>
                <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
                <script>
                    const socket = io("http://localhost:5000");

                    // Función para enviar el mensaje
                    function sendMessage() {
                        const message = document.getElementById("message").value;
                        socket.emit('send_message', message);  // Enviar el mensaje al servidor
                    }

                    // Escuchar el mensaje del servidor
                    socket.on('server_message', function(data) {
                        console.log("Mensaje recibido del servidor:", data);
                        alert(data.data);  // Mostrar el mensaje en una alerta
                    });
                </script>
            </head>
            <body>
                <h1>WebSocket en Flask</h1>
                <input id="message" value="Mensaje">
                <button onclick="sendMessage()">Enviar</button>
            </body>
            </html>
                    
                    
                    """

@app.route('/links')
def hello():
    print("HELLO")

@socketio.on("connect")
def handle_connect():
    print("Cliente conectado.")

@socketio.on("disconnect")
def handle_disconnect():
    print("Cliente desconectado.")

def send_icmp_packet(packet_info):
    """
    Función para enviar información sobre un paquete ICMP
    a todos los clientes conectados.
    """
    socketio.emit("icmp_packet", packet_info)
    ##print("Paquete ICMP enviado:", packet_info)

def start_websocket_server():
    """Inicia el servidor WebSocket."""
    socketio.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    start_websocket_server()
