"""
Probar descarga de archivo desde S3
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage import S3StorageService

def test_download():
    print("=" * 60)
    print("PRUEBA DE DESCARGA DE ARCHIVO")
    print("=" * 60)
    
    try:
        # Crear servicio S3
        s3_service = S3StorageService()
        
        # Archivo de prueba que existe en el bucket
        test_file = "solicitudes/2026/01/5/arte/fbe55bb0c6ec487997568d19faa370cc.pdf"
        
        print(f"\n📁 Archivo: {test_file}")
        print(f"🔗 Generando URL de descarga...")
        
        # Generar URL de descarga
        url = s3_service.get_download_url(test_file)
        
        print(f"\n✅ URL generada exitosamente:")
        print(f"\n{url}\n")
        
        # Verificar que contiene la región
        if 'us-east-2' in url:
            print("✅ La URL incluye la región us-east-2")
        else:
            print("⚠️  La URL no incluye la región us-east-2")
        
        # Verificar que usa HTTPS
        if url.startswith('https://'):
            print("✅ La URL usa HTTPS")
        else:
            print("⚠️  La URL no usa HTTPS")
        
        print("\n" + "=" * 60)
        print("Puedes copiar y pegar esta URL en tu navegador para probar")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_download()
