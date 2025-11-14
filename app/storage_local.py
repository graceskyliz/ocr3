# app/storage_local.py
import os
import hashlib
import uuid
from pathlib import Path
from typing import BinaryIO
from fastapi import HTTPException

from app.settings import settings

def ensure_upload_dir():
    """Asegura que el directorio de uploads existe."""
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path

def save_file_local(file_data: BinaryIO, tenant_id: str, doc_id: str, filename: str) -> str:
    """
    Guarda un archivo en el sistema de archivos local.
    
    Args:
        file_data: Datos binarios del archivo
        tenant_id: ID del tenant
        doc_id: ID del documento
        filename: Nombre original del archivo
    
    Returns:
        Ruta relativa donde se guardó el archivo
    """
    # Crear estructura de directorios: uploads/{tenant_id}/{doc_id}/
    upload_dir = ensure_upload_dir()
    tenant_dir = upload_dir / tenant_id
    doc_dir = tenant_dir / str(doc_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar archivo
    file_path = doc_dir / filename
    
    try:
        with open(file_path, 'wb') as f:
            content = file_data.read()
            f.write(content)
        
        # Retornar ruta relativa desde UPLOAD_DIR
        relative_path = f"{tenant_id}/{doc_id}/{filename}"
        return relative_path
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar archivo: {str(e)}"
        )

def get_file_path(storage_key: str) -> str:
    """
    Obtiene la ruta absoluta de un archivo desde su storage_key.
    
    Args:
        storage_key: Ruta relativa del archivo (ej: "tenant_id/doc_id/file.pdf")
    
    Returns:
        Ruta absoluta al archivo
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    file_path = upload_dir / storage_key
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Archivo no encontrado: {storage_key}"
        )
    
    return str(file_path)

def delete_file(storage_key: str) -> bool:
    """
    Elimina un archivo del sistema de archivos local.
    
    Args:
        storage_key: Ruta relativa del archivo
    
    Returns:
        True si se eliminó correctamente
    """
    try:
        file_path = Path(settings.UPLOAD_DIR) / storage_key
        if file_path.exists():
            file_path.unlink()
            
            # Intentar eliminar directorios vacíos
            try:
                file_path.parent.rmdir()  # doc_id dir
                file_path.parent.parent.rmdir()  # tenant_id dir
            except OSError:
                pass  # Directorio no vacío, no hay problema
            
            return True
        return False
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar archivo: {str(e)}"
        )

def sha256_bytes(data: bytes) -> str:
    """Calcula el hash SHA256 de datos binarios."""
    return hashlib.sha256(data).hexdigest()

def get_file_size(storage_key: str) -> int:
    """Obtiene el tamaño de un archivo en bytes."""
    file_path = Path(settings.UPLOAD_DIR) / storage_key
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return file_path.stat().st_size
