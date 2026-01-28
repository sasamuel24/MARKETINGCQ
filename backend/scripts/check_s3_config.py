"""
Script para verificar y configurar permisos del bucket S3
"""
import sys
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings

def check_bucket_config():
    """Verificar configuración del bucket S3"""
    print("=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN DEL BUCKET S3")
    print("=" * 60)
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )
    
    bucket_name = settings.AWS_BUCKET_NAME
    
    print(f"\n📦 Bucket: {bucket_name}")
    print(f"🌍 Región: {settings.AWS_REGION}")
    
    # 1. Verificar ubicación del bucket
    try:
        location = s3_client.get_bucket_location(Bucket=bucket_name)
        print(f"\n✅ Ubicación del bucket: {location['LocationConstraint']}")
    except ClientError as e:
        print(f"\n❌ Error al obtener ubicación: {e}")
    
    # 2. Verificar CORS
    try:
        cors = s3_client.get_bucket_cors(Bucket=bucket_name)
        print(f"\n✅ CORS configurado:")
        print(json.dumps(cors['CORSRules'], indent=2))
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
            print(f"\n⚠️  CORS no configurado")
            print("\n🔧 Configurando CORS...")
            try:
                cors_config = {
                    'CORSRules': [
                        {
                            'AllowedHeaders': ['*'],
                            'AllowedMethods': ['GET', 'HEAD'],
                            'AllowedOrigins': ['*'],
                            'ExposeHeaders': ['ETag'],
                            'MaxAgeSeconds': 3000
                        }
                    ]
                }
                s3_client.put_bucket_cors(
                    Bucket=bucket_name,
                    CORSConfiguration=cors_config
                )
                print("✅ CORS configurado exitosamente")
            except ClientError as ce:
                print(f"❌ Error al configurar CORS: {ce}")
        else:
            print(f"\n❌ Error al verificar CORS: {e}")
    
    # 3. Verificar política del bucket
    try:
        policy = s3_client.get_bucket_policy(Bucket=bucket_name)
        print(f"\n✅ Política del bucket configurada:")
        print(json.dumps(json.loads(policy['Policy']), indent=2))
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
            print(f"\n⚠️  No hay política del bucket configurada")
        else:
            print(f"\n❌ Error al verificar política: {e}")
    
    # 4. Verificar bloqueo de acceso público
    try:
        public_access = s3_client.get_public_access_block(Bucket=bucket_name)
        print(f"\n📋 Configuración de bloqueo de acceso público:")
        config = public_access['PublicAccessBlockConfiguration']
        print(f"   BlockPublicAcls: {config['BlockPublicAcls']}")
        print(f"   IgnorePublicAcls: {config['IgnorePublicAcls']}")
        print(f"   BlockPublicPolicy: {config['BlockPublicPolicy']}")
        print(f"   RestrictPublicBuckets: {config['RestrictPublicBuckets']}")
    except ClientError as e:
        print(f"\n⚠️  No se pudo verificar bloqueo de acceso público: {e}")
    
    # 5. Probar generación de URL firmada
    print(f"\n🔗 Probando generación de URL firmada...")
    try:
        # Buscar primer archivo en el bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        
        if 'Contents' in response and len(response['Contents']) > 0:
            test_key = response['Contents'][0]['Key']
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': test_key
                },
                ExpiresIn=3600
            )
            print(f"✅ URL firmada generada exitosamente")
            print(f"   Archivo: {test_key}")
            print(f"   URL: {url[:100]}...")
            
            # Verificar formato de URL
            if settings.AWS_REGION in url:
                print(f"✅ URL incluye región correctamente")
            else:
                print(f"⚠️  URL no incluye región: {settings.AWS_REGION}")
        else:
            print("⚠️  No hay archivos en el bucket para probar")
    except Exception as e:
        print(f"❌ Error al generar URL: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_bucket_config()
