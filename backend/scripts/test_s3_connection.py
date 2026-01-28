"""
Script para probar la conexión a AWS S3
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Cargar variables de entorno
load_dotenv()

def test_s3_connection():
    """
    Prueba la conexión a AWS S3 y lista los objetos del bucket
    """
    print("=" * 60)
    print("PRUEBA DE CONEXIÓN A AWS S3")
    print("=" * 60)
    
    # Obtener credenciales desde .env
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")
    bucket_name = os.getenv("AWS_BUCKET_NAME")
    
    print("\n📋 Configuración:")
    print(f"   AWS Region: {aws_region}")
    print(f"   Bucket Name: {bucket_name}")
    print(f"   Access Key: {aws_access_key[:10]}..." if aws_access_key else "   Access Key: No configurado")
    print(f"   Secret Key: {'*' * 20}" if aws_secret_key else "   Secret Key: No configurado")
    
    if not all([aws_access_key, aws_secret_key, aws_region, bucket_name]):
        print("\n❌ ERROR: Faltan credenciales de AWS en el archivo .env")
        return False
    
    try:
        # Crear cliente S3
        print("\n🔄 Creando cliente S3...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Verificar que el bucket existe
        print(f"\n🔍 Verificando acceso al bucket '{bucket_name}'...")
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' accesible correctamente")
        
        # Listar objetos del bucket (primeros 10)
        print(f"\n📂 Listando objetos en el bucket...")
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            MaxKeys=10
        )
        
        if 'Contents' in response:
            print(f"\n📁 Se encontraron {response.get('KeyCount', 0)} objetos (mostrando primeros 10):")
            for obj in response['Contents']:
                size_kb = obj['Size'] / 1024
                print(f"   - {obj['Key']} ({size_kb:.2f} KB)")
        else:
            print("\n📁 El bucket está vacío")
        
        # Probar creación de un archivo de prueba
        print("\n🧪 Probando subida de archivo de prueba...")
        test_key = "test/connection_test.txt"
        test_content = "Prueba de conexión a S3 desde MarketingCQ"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print(f"✅ Archivo de prueba subido correctamente: {test_key}")
        
        # Verificar que se puede leer
        print(f"\n📖 Leyendo archivo de prueba...")
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=test_key
        )
        content = response['Body'].read().decode('utf-8')
        print(f"✅ Contenido leído: '{content}'")
        
        # Eliminar archivo de prueba
        print(f"\n🗑️  Eliminando archivo de prueba...")
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=test_key
        )
        print(f"✅ Archivo de prueba eliminado correctamente")
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("=" * 60)
        return True
        
    except NoCredentialsError:
        print("\n❌ ERROR: No se encontraron credenciales de AWS")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"\n❌ ERROR AWS: {error_code}")
        print(f"   Mensaje: {error_message}")
        
        if error_code == '403' or error_code == 'AccessDenied':
            print("\n💡 Sugerencias:")
            print("   - Verifica que las credenciales sean correctas")
            print("   - Verifica que el usuario IAM tenga permisos para acceder al bucket")
            print("   - Verifica que el bucket exista en la región especificada")
        elif error_code == '404' or error_code == 'NoSuchBucket':
            print("\n💡 Sugerencias:")
            print("   - Verifica que el nombre del bucket sea correcto")
            print("   - Verifica que el bucket exista en la región especificada")
        
        return False
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {str(e)}")
        print(f"   Tipo: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_s3_connection()
    sys.exit(0 if success else 1)
