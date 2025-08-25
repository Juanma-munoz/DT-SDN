# server.py
from flask import Flask, jsonify, request

app = Flask(__name__)

# Ruta raíz
@app.route('/')
def home():
    return "¡Hola, este es mi servidor Flask!"

# Ruta que devuelve datos JSON
@app.route('/api/data', methods=['GET'])
def get_data():
    data = {
        'mensaje': 'Hola desde el servidor Flask',
        'estado': 'funcionando'
    }
    return jsonify(data)

# Ruta que recibe datos POST
@app.route('/api/echo', methods=['POST'])
def echo():
    data = request.json  # Obtiene el JSON enviado
    return jsonify({
        'datos_recibidos': data
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1000, debug=True)
