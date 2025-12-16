import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from app.rutas import app
from dotenv import load_dotenv  
load_dotenv()
if __name__ == '__main__':
   
    print("ALMAS CON COLA - Sistema de Gestión")
    


    app.run(
        debug=True,           
        host='0.0.0.0',      
        port=5000,            
        threaded=True       
    )

