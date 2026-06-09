import os
from dotenv import load_dotenv
from app import create_app

# Cargar variables de entorno
load_dotenv()

# Crear aplicación con Factory Pattern
app, db = create_app()

if __name__ == '__main__':
    app.run(
        debug=app.debug,
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 5000)),
        threaded=True
    )

