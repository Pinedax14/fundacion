"""
Utilidades para manejo seguro de uploads
"""

import os
import secrets
import mimetypes
from werkzeug.utils import secure_filename
from flask import current_app


class UploadManager:
    """Gestor seguro de uploads de archivos"""
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_MIME_TYPES = {
        'image/png',
        'image/jpeg',
        'image/gif'
    }
    
    @staticmethod
    def allowed_file(filename):
        """Verifica si el archivo tiene extensión permitida"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in UploadManager.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_mime_type(filepath):
        """Valida el tipo MIME del archivo"""
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type not in UploadManager.ALLOWED_MIME_TYPES:
            os.remove(filepath)
            raise ValueError(f'Tipo de archivo no permitido: {mime_type}')
    
    @staticmethod
    def save_upload(file, folder, prefix=''):
        """
        Guarda un archivo de forma segura
        
        Args:
            file: FileStorage de Flask
            folder: Carpeta destino relativa a static
            prefix: Prefijo para el nombre del archivo
        
        Returns:
            str: Nombre del archivo guardado o None si hay error
        """
        try:
            # Validaciones
            if not file or file.filename == '':
                raise ValueError('No file selected')
            
            if not UploadManager.allowed_file(file.filename):
                raise ValueError('File type not allowed')
            
            if file.content_length > current_app.config['MAX_CONTENT_LENGTH']:
                raise ValueError('File too large')
            
            # Generar nombre único con secret
            filename_base = secure_filename(file.filename.rsplit('.', 1)[0])
            extension = secure_filename(file.filename.rsplit('.', 1)[1])
            random_suffix = secrets.token_hex(8)
            nuevo_nombre = f"{prefix}_{filename_base}_{random_suffix}.{extension}" if prefix else f"{filename_base}_{random_suffix}.{extension}"
            
            # Crear carpeta si no existe
            upload_path = os.path.join(current_app.static_folder, folder)
            os.makedirs(upload_path, exist_ok=True)
            
            # Guardar archivo
            filepath = os.path.join(upload_path, nuevo_nombre)
            file.save(filepath)
            
            # Validar MIME type
            UploadManager.validate_mime_type(filepath)
            
            current_app.logger.info(f"Upload guardado: {nuevo_nombre}")
            
            # Retornar solo la parte relativa
            return nuevo_nombre
        
        except Exception as e:
            current_app.logger.error(f"Error en upload: {str(e)}")
            raise


class FileUtils:
    """Utilidades para manejo de archivos"""
    
    @staticmethod
    def delete_file(filepath):
        """Elimina archivo de forma segura"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            current_app.logger.error(f"Error eliminando archivo {filepath}: {str(e)}")
        return False
    
    @staticmethod
    def get_file_size(filepath):
        """Obtiene el tamaño de un archivo en MB"""
        try:
            return os.path.getsize(filepath) / (1024 * 1024)
        except:
            return 0
