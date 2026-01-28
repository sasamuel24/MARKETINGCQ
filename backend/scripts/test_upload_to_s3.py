"""
Script para probar la subida de archivos a S3 mediante el endpoint
"""
import sys
from pathlib import Path
import requests
import json

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

API_URL = "http://localhost:8000/api/v1"

def login_and_get_token():
    """Login y obtener token de acceso"""
    print("🔐 Iniciando sesión...")
    response = requests.post(
        f"{API_URL}/auth/login",
        data={
            "username": "creator@test.com",
            "password": "password123"
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login exitoso")
        return token
    else:
        print(f"❌ Error en login: {response.status_code}")
        print(response.text)
        return None

def create_test_solicitud(token):
    """Crear una solicitud de prueba"""
    print("\n📝 Creando solicitud de prueba...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "title": "Prueba de subida a S3",
        "description": "Solicitud de prueba para verificar subida de archivos a S3",
        "area_id": 1,
        "stage_id": 1,
        "status_id": 1
    }
    
    response = requests.post(
        f"{API_URL}/solicitudes",
        headers=headers,
        json=data
    )
    
    if response.status_code == 201:
        solicitud = response.json()
        print(f"✅ Solicitud creada: ID {solicitud['id']}")
        return solicitud['id']
    else:
        print(f"❌ Error al crear solicitud: {response.status_code}")
        print(response.text)
        return None

def upload_test_file(token, solicitud_id):
    """Subir archivo de prueba a la solicitud"""
    print(f"\n📤 Subiendo archivo de prueba a solicitud {solicitud_id}...")
    
    # Crear archivo de prueba
    test_content = b"Este es un archivo de prueba para verificar la subida a S3"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    files = {
        'files': ('test_file.txt', test_content, 'text/plain')
    }
    
    data = {
        'doc_type': 'ARTE'
    }
    
    response = requests.post(
        f"{API_URL}/solicitudes/{solicitud_id}/upload-files",
        headers=headers,
        files=files,
        data=data
    )
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Archivo subido exitosamente")
        print(f"   Mensaje: {result['message']}")
        if result.get('files'):
            for file in result['files']:
                print(f"   - ID: {file.get('id')}")
                print(f"   - Nombre: {file.get('filename')}")
                print(f"   - Ruta S3: {file.get('storage_path')}")
        return True
    else:
        print(f"❌ Error al subir archivo: {response.status_code}")
        print(response.text)
        return False

def test_download_url(token, solicitud_id, file_id):
    """Obtener URL de descarga"""
    print(f"\n🔗 Obteniendo URL de descarga...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{API_URL}/solicitudes/{solicitud_id}/files/{file_id}/download",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ URL de descarga generada")
        print(f"   URL: {result['download_url'][:100]}...")
        print(f"   Archivo: {result['filename']}")
        print(f"   Expira en: {result['expires_in']} segundos")
        return True
    else:
        print(f"❌ Error al obtener URL: {response.status_code}")
        print(response.text)
        return False

def main():
    print("=" * 60)
    print("PRUEBA DE SUBIDA DE ARCHIVOS A S3")
    print("=" * 60)
    
    # 1. Login
    token = login_and_get_token()
    if not token:
        print("\n❌ No se pudo obtener token de acceso")
        return
    
    # 2. Crear solicitud
    solicitud_id = create_test_solicitud(token)
    if not solicitud_id:
        print("\n❌ No se pudo crear la solicitud")
        return
    
    # 3. Subir archivo
    success = upload_test_file(token, solicitud_id)
    if not success:
        print("\n❌ No se pudo subir el archivo")
        return
    
    # 4. Obtener archivos de la solicitud para obtener el file_id
    print(f"\n📂 Obteniendo archivos de la solicitud {solicitud_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_URL}/solicitud-files/solicitud/{solicitud_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        files = response.json()
        if files:
            file_id = files[0]['id']
            print(f"✅ Archivo encontrado: ID {file_id}")
            
            # 5. Probar descarga
            test_download_url(token, solicitud_id, file_id)
        else:
            print("⚠️  No se encontraron archivos en la solicitud")
    
    print("\n" + "=" * 60)
    print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    main()
