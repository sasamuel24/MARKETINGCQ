"""
Script de prueba para envío de correos
"""
from core.email import email_service

# Correo de prueba del destinatario
TEST_EMAIL = "laura.moreno@cafequindio.com.co"

def test_approval_notification():
    """Probar notificación de nueva solicitud a aprobador"""
    print("\n=== Probando: Notificación de Nueva Solicitud ===")
    result = email_service.send_approval_notification(
        to_emails=[TEST_EMAIL],
        solicitud_id=123,
        solicitud_title="Arte para campaña de San Valentín 2026",
        stage_name="Revisión Laura Mota (Mercadeo)",
        creator_name="Juliana Amézquita"
    )
    print(f"Resultado: {'✓ Enviado' if result else '✗ Error'}")
    return result

def test_adjustment_request():
    """Probar notificación de ajustes solicitados"""
    print("\n=== Probando: Solicitud de Ajustes ===")
    result = email_service.send_adjustment_request_notification(
        to_email=TEST_EMAIL,
        solicitud_id=123,
        solicitud_title="Arte para campaña de San Valentín 2026",
        comment="Por favor ajustar el logo, debe ser más grande y centrado. También revisar los colores institucionales.",
        reviewer_name="Laura Mota"
    )
    print(f"Resultado: {'✓ Enviado' if result else '✗ Error'}")
    return result

def test_approval_to_creator():
    """Probar notificación de aprobación al creador"""
    print("\n=== Probando: Notificación de Aprobación ===")
    result = email_service.send_approval_notification_to_creator(
        to_email=TEST_EMAIL,
        solicitud_id=123,
        solicitud_title="Arte para campaña de San Valentín 2026",
        approver_name="Laura Mota",
        stage_name="Revisión Laura Mota (Mercadeo)",
        is_final=False
    )
    print(f"Resultado: {'✓ Enviado' if result else '✗ Error'}")
    return result

def test_final_approval():
    """Probar notificación de aprobación final"""
    print("\n=== Probando: Aprobación Final ===")
    result = email_service.send_approval_notification_to_creator(
        to_email=TEST_EMAIL,
        solicitud_id=123,
        solicitud_title="Arte para campaña de San Valentín 2026",
        approver_name="Mariana Cardenas",
        stage_name="Revisión Gerencia Mercadeo",
        is_final=True
    )
    print(f"Resultado: {'✓ Enviado' if result else '✗ Error'}")
    return result

def test_rejection():
    """Probar notificación de rechazo"""
    print("\n=== Probando: Notificación de Rechazo ===")
    result = email_service.send_rejection_notification(
        to_email=TEST_EMAIL,
        solicitud_id=123,
        solicitud_title="Arte para campaña de San Valentín 2026",
        comment="El diseño no cumple con los lineamientos de marca. Los colores no son apropiados y el mensaje no es claro.",
        reviewer_name="Laura Mota"
    )
    print(f"Resultado: {'✓ Enviado' if result else '✗ Error'}")
    return result

def test_all():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*60)
    print("PRUEBA DE ENVÍO DE CORREOS - MARKETINGCQ")
    print("="*60)
    print(f"Destinatario de prueba: {TEST_EMAIL}")
    
    results = []
    
    # Probar cada tipo de correo
    results.append(("Notificación Nueva Solicitud", test_approval_notification()))
    results.append(("Solicitud de Ajustes", test_adjustment_request()))
    results.append(("Aprobación (Etapa Intermedia)", test_approval_to_creator()))
    results.append(("Aprobación Final", test_final_approval()))
    results.append(("Rechazo", test_rejection()))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    for name, result in results:
        status = "✓ EXITOSO" if result else "✗ FALLIDO"
        print(f"{name:.<45} {status}")
    
    successful = sum(1 for _, r in results if r)
    print(f"\nTotal: {successful}/{len(results)} correos enviados exitosamente")
    print("="*60)

if __name__ == "__main__":
    # Menú interactivo
    print("\nSelecciona el tipo de correo a probar:")
    print("1. Notificación de nueva solicitud (a aprobador)")
    print("2. Solicitud de ajustes (a creador)")
    print("3. Aprobación intermedia (a creador)")
    print("4. Aprobación final (a creador)")
    print("5. Rechazo (a creador)")
    print("6. Probar todos los correos")
    print("0. Salir")
    
    choice = input("\nOpción: ").strip()
    
    if choice == "1":
        test_approval_notification()
    elif choice == "2":
        test_adjustment_request()
    elif choice == "3":
        test_approval_to_creator()
    elif choice == "4":
        test_final_approval()
    elif choice == "5":
        test_rejection()
    elif choice == "6":
        test_all()
    elif choice == "0":
        print("Saliendo...")
    else:
        print("Opción inválida")
