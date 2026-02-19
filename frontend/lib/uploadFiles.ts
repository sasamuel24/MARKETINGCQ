/**
 * Sube archivos directamente a S3 usando presigned URLs.
 * Evita pasar por API Gateway (límite 10MB).
 *
 * Flujo:
 * 1. Pide presigned URLs al backend
 * 2. Sube cada archivo directo a S3 con PUT
 * 3. Registra cada archivo en la BD
 */
export async function uploadFilesWithPresignedUrl(
  apiUrl: string,
  token: string,
  solicitudId: number,
  files: File[],
  docType: string = "ARTE"
): Promise<void> {
  // 1. Pedir presigned URLs al backend
  const filesInfo = files.map((f) => ({
    filename: f.name,
    content_type: f.type || "application/octet-stream",
    doc_type: docType,
  }));

  const presignedRes = await fetch(
    `${apiUrl}/api/v1/solicitudes/${solicitudId}/presigned-upload`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(filesInfo),
    }
  );

  if (!presignedRes.ok) {
    const err = await presignedRes.json().catch(() => ({}));
    throw new Error(err.detail || "Error al obtener URLs de subida");
  }

  const { urls } = await presignedRes.json();

  // 2. Subir cada archivo directo a S3
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const urlInfo = urls[i];

    const s3Res = await fetch(urlInfo.upload_url, {
      method: "PUT",
      headers: {
        "Content-Type": file.type || "application/octet-stream",
      },
      body: file,
    });

    if (!s3Res.ok) {
      throw new Error(`Error al subir archivo "${file.name}" a S3 (${s3Res.status})`);
    }

    // 3. Registrar en la BD
    const registerRes = await fetch(
      `${apiUrl}/api/v1/solicitudes/${solicitudId}/register-file`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          storage_path: urlInfo.storage_path,
          filename: urlInfo.filename,
          content_type: urlInfo.content_type,
          size_bytes: file.size,
          doc_type: urlInfo.doc_type,
        }),
      }
    );

    if (!registerRes.ok) {
      const err = await registerRes.json().catch(() => ({}));
      throw new Error(err.detail || `Error al registrar archivo "${file.name}"`);
    }
  }
}
