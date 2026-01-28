"""
Servicio de almacenamiento de archivos en AWS S3
"""
import os
import uuid
from datetime import datetime
from typing import Optional, BinaryIO
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile, HTTPException, status

from core.config import settings


class S3StorageService:
    """Servicio para gestionar almacenamiento de archivos en AWS S3"""
    
    def __init__(self):
        """Inicializar cliente S3 con credenciales desde configuración"""
        self.aws_access_key = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
        self.aws_region = settings.AWS_REGION
        self.bucket_name = settings.AWS_BUCKET_NAME
        
        if not all([self.aws_access_key, self.aws_secret_key, self.bucket_name]):
            raise ValueError(
                "Faltan credenciales de AWS S3 en variables de entorno. "
                "Verifica AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY y AWS_BUCKET_NAME en el archivo .env"
            )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region,
            config=boto3.session.Config(
                signature_version='s3v4',
                s3={'addressing_style': 'virtual'}
            )
        )
    
    def generate_file_path(
        self,
        solicitud_id: int,
        filename: str,
        doc_type: str = "ARTE"
    ) -> str:
        """
        Generar ruta única para el archivo en S3
        
        Args:
            solicitud_id: ID de la solicitud
            filename: Nombre original del archivo
            doc_type: Tipo de documento (ARTE, BRIEF, EVIDENCIA)
            
        Returns:
            Ruta del archivo en S3
        """
        # Obtener extensión del archivo
        file_ext = Path(filename).suffix
        
        # Generar nombre único con UUID
        unique_name = f"{uuid.uuid4().hex}{file_ext}"
        
        # Crear estructura de carpetas: solicitudes/{año}/{mes}/{solicitud_id}/{doc_type}/{archivo}
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        s3_path = f"solicitudes/{year}/{month}/{solicitud_id}/{doc_type.lower()}/{unique_name}"
        return s3_path
    
    async def upload_file(
        self,
        file: UploadFile,
        solicitud_id: int,
        doc_type: str = "ARTE"
    ) -> dict:
        """
        Subir archivo a S3
        
        Args:
            file: Archivo a subir (FastAPI UploadFile)
            solicitud_id: ID de la solicitud
            doc_type: Tipo de documento
            
        Returns:
            Dict con información del archivo subido:
            - storage_path: Ruta en S3
            - filename: Nombre original
            - content_type: Tipo MIME
            - size_bytes: Tamaño en bytes
            - storage_provider: "s3"
            
        Raises:
            HTTPException: Si hay error al subir el archivo
        """
        try:
            # Generar ruta única
            s3_path = self.generate_file_path(solicitud_id, file.filename, doc_type)
            
            # Leer contenido del archivo
            content = await file.read()
            size_bytes = len(content)
            
            # Subir a S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_path,
                Body=content,
                ContentType=file.content_type or "application/octet-stream",
                Metadata={
                    "solicitud_id": str(solicitud_id),
                    "doc_type": doc_type,
                    "original_filename": file.filename
                }
            )
            
            # Resetear el cursor del archivo por si se necesita leer de nuevo
            await file.seek(0)
            
            return {
                "storage_path": s3_path,
                "filename": file.filename,
                "content_type": file.content_type or "application/octet-stream",
                "size_bytes": size_bytes,
                "storage_provider": "s3",
                "doc_type": doc_type
            }
            
        except NoCredentialsError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Credenciales de AWS no configuradas"
            )
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al subir archivo a S3: {e.response['Error']['Message']}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inesperado al subir archivo: {str(e)}"
            )
    
    def get_download_url(
        self,
        storage_path: str,
        expiration: int = 3600
    ) -> str:
        """
        Generar URL temporal para descargar archivo
        
        Args:
            storage_path: Ruta del archivo en S3
            expiration: Tiempo de expiración en segundos (default: 1 hora)
            
        Returns:
            URL temporal firmada
        """
        try:
            # Generar URL con endpoint regional explícito
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_path
                },
                ExpiresIn=expiration,
                HttpMethod='GET'
            )
            
            # Asegurar que la URL usa el endpoint regional correcto
            # Reemplazar el dominio genérico por el regional si es necesario
            if '.s3.amazonaws.com/' in url and self.aws_region != 'us-east-1':
                url = url.replace(
                    f'{self.bucket_name}.s3.amazonaws.com',
                    f'{self.bucket_name}.s3.{self.aws_region}.amazonaws.com'
                )
            
            return url
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al generar URL de descarga: {e.response['Error']['Message']}"
            )
    
    def delete_file(self, storage_path: str) -> bool:
        """
        Eliminar archivo de S3
        
        Args:
            storage_path: Ruta del archivo en S3
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return True
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al eliminar archivo de S3: {e.response['Error']['Message']}"
            )
    
    def download_file(self, storage_path: str) -> bytes:
        """
        Descargar archivo de S3 como bytes
        
        Args:
            storage_path: Ruta del archivo en S3
            
        Returns:
            Contenido del archivo como bytes
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Archivo no encontrado: {storage_path}"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al descargar archivo de S3: {e.response['Error']['Message']}"
            )
    
    def file_exists(self, storage_path: str) -> bool:
        """
        Verificar si un archivo existe en S3
        
        Args:
            storage_path: Ruta del archivo en S3
            
        Returns:
            True si el archivo existe
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return True
        except ClientError:
            return False


# Instancia global del servicio
s3_storage = None

def get_s3_storage() -> S3StorageService:
    """Dependency para obtener instancia del servicio S3"""
    global s3_storage
    if s3_storage is None:
        s3_storage = S3StorageService()
    return s3_storage
