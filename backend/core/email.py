"""
Servicio de email usando Microsoft Graph API
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import requests
import msal
from core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio para enviar correos usando Microsoft Graph API"""
    
    def __init__(self):
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.email_from = settings.EMAIL_FROM
        self.frontend_url = settings.FRONTEND_URL
        
    def _get_access_token(self) -> Optional[str]:
        """
        Obtener token de acceso usando MSAL (Microsoft Authentication Library)
        """
        try:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret
            )
            
            # Scopes para Microsoft Graph
            scopes = ["https://graph.microsoft.com/.default"]
            
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                return result["access_token"]
            else:
                logger.error(f"Error getting access token: {result.get('error_description')}")
                return None
                
        except Exception as e:
            logger.error(f"Exception getting access token: {str(e)}")
            return None
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """
        Enviar correo usando Microsoft Graph API
        
        Args:
            to_emails: Lista de correos destinatarios
            subject: Asunto del correo
            body_html: Cuerpo del correo en HTML
            body_text: Cuerpo del correo en texto plano (opcional)
            
        Returns:
            True si el correo se envió exitosamente, False en caso contrario
        """
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            logger.warning("Azure AD credentials not configured, skipping email")
            return False
        
        try:
            token = self._get_access_token()
            if not token:
                return False
            
            # Construir el mensaje
            recipients = [{"emailAddress": {"address": email}} for email in to_emails]
            
            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": body_html
                    },
                    "toRecipients": recipients
                },
                "saveToSentItems": "true"
            }
            
            # Enviar el correo
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Usar el endpoint /sendMail del usuario remitente
            endpoint = f"https://graph.microsoft.com/v1.0/users/{self.email_from}/sendMail"
            
            response = requests.post(endpoint, headers=headers, json=message)
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {to_emails}")
                return True
            else:
                logger.error(f"Error sending email: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Exception sending email: {str(e)}")
            return False
    
    def send_approval_notification(
        self,
        to_emails: List[str],
        solicitud_id: int,
        solicitud_title: str,
        stage_name: str,
        creator_name: str
    ) -> bool:
        """
        Enviar notificación de solicitud pendiente de aprobación
        
        Args:
            to_emails: Lista de correos de los aprobadores
            solicitud_id: ID de la solicitud
            solicitud_title: Título de la solicitud
            stage_name: Nombre de la etapa actual
            creator_name: Nombre del creador
            
        Returns:
            True si el correo se envió exitosamente
        """
        subject = f"Nueva solicitud pendiente de aprobación: {solicitud_title}"
        
        solicitud_url = f"{self.frontend_url}/solicitudes/{solicitud_id}"
        
        body_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8fafb; }}
                .header {{ background: linear-gradient(135deg, #00829a 0%, #00a3b4 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .header h2 {{ margin: 0; font-size: 24px; font-weight: bold; }}
                .content {{ background-color: white; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .detail {{ margin: 15px 0; padding: 10px; background-color: #f8fafb; border-radius: 4px; }}
                .detail strong {{ color: #00829a; font-weight: 600; }}
                .button {{ display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #00829a 0%, #00a3b4 100%); color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; box-shadow: 0 2px 4px rgba(0,130,154,0.3); }}
                .button:hover {{ opacity: 0.9; }}
                .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 12px; margin-top: 20px; }}
                .brand {{ color: #00829a; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📋 Nueva Solicitud de Aprobación</h2>
                </div>
                <div class="content">
                    <p>Hola,</p>
                    <p>Se te ha asignado una nueva solicitud que requiere tu aprobación:</p>
                    
                    <div class="detail">
                        <strong>Solicitud:</strong> {solicitud_title}
                    </div>
                    <div class="detail">
                        <strong>ID:</strong> #{solicitud_id}
                    </div>
                    <div class="detail">
                        <strong>Etapa:</strong> {stage_name}
                    </div>
                    <div class="detail">
                        <strong>Creado por:</strong> {creator_name}
                    </div>
                    
                    <p style="margin-top: 30px; text-align: center;">
                        <a href="{solicitud_url}" class="button">Ver Solicitud</a>
                    </p>
                    
                    <p style="color: #6c757d; font-size: 14px; margin-top: 20px;">
                        Por favor, revisa la solicitud y proporciona tu aprobación o comentarios.
                    </p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no responder.</p>
                    <p><span class="brand">CAFÉ QUINDÍO</span> - Sistema de Gestión de Marketing</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_emails, subject, body_html)
    
    def send_adjustment_request_notification(
        self,
        to_email: str,
        solicitud_id: int,
        solicitud_title: str,
        comment: str,
        reviewer_name: str
    ) -> bool:
        """
        Enviar notificación de solicitud de ajustes al creador
        
        Args:
            to_email: Correo del creador
            solicitud_id: ID de la solicitud
            solicitud_title: Título de la solicitud
            comment: Comentario del revisor
            reviewer_name: Nombre del revisor
            
        Returns:
            True si el correo se envió exitosamente
        """
        subject = f"Ajustes solicitados en: {solicitud_title}"
        
        solicitud_url = f"{self.frontend_url}/solicitudes/{solicitud_id}"
        
        body_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8fafb; }}
                .header {{ background: linear-gradient(135deg, #96c121 0%, #c2d500 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .header h2 {{ margin: 0; font-size: 24px; font-weight: bold; }}
                .content {{ background-color: white; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .detail {{ margin: 15px 0; padding: 10px; background-color: #f8fafb; border-radius: 4px; }}
                .detail strong {{ color: #96c121; font-weight: 600; }}
                .comment {{ background-color: #fffbea; padding: 20px; border-left: 4px solid #96c121; margin: 20px 0; border-radius: 4px; }}
                .button {{ display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #96c121 0%, #c2d500 100%); color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; box-shadow: 0 2px 4px rgba(150,193,33,0.3); }}
                .button:hover {{ opacity: 0.9; }}
                .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 12px; margin-top: 20px; }}
                .brand {{ color: #00829a; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>⚠️ Ajustes Solicitados</h2>
                </div>
                <div class="content">
                    <p>Hola,</p>
                    <p>Se han solicitado ajustes en tu solicitud:</p>
                    
                    <div class="detail">
                        <strong>Solicitud:</strong> {solicitud_title}
                    </div>
                    <div class="detail">
                        <strong>ID:</strong> #{solicitud_id}
                    </div>
                    <div class="detail">
                        <strong>Revisado por:</strong> {reviewer_name}
                    </div>
                    
                    <div class="comment">
                        <strong style="color: #96c121;">Comentario:</strong>
                        <p style="margin: 10px 0 0 0;">{comment}</p>
                    </div>
                    
                    <p style="margin-top: 30px; text-align: center;">
                        <a href="{solicitud_url}/upload" class="button">Subir Nueva Versión</a>
                    </p>
                    
                    <p style="color: #6c757d; font-size: 14px; margin-top: 20px;">
                        Por favor, revisa los comentarios y sube una nueva versión con los ajustes solicitados.
                    </p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no responder.</p>
                    <p><span class="brand">CAFÉ QUINDÍO</span> - Sistema de Gestión de Marketing</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email([to_email], subject, body_html)
    
    def send_approval_notification_to_creator(
        self,
        to_email: str,
        solicitud_id: int,
        solicitud_title: str,
        approver_name: str,
        stage_name: str,
        is_final: bool = False
    ) -> bool:
        """
        Enviar notificación de aprobación al creador
        
        Args:
            to_email: Correo del creador
            solicitud_id: ID de la solicitud
            solicitud_title: Título de la solicitud
            approver_name: Nombre del aprobador
            stage_name: Nombre de la etapa aprobada
            is_final: Si es la aprobación final
            
        Returns:
            True si el correo se envió exitosamente
        """
        subject = f"{'Aprobación final' if is_final else 'Solicitud aprobada'}: {solicitud_title}"
        
        solicitud_url = f"{self.frontend_url}/solicitudes/{solicitud_id}"
        
        header_color = "linear-gradient(135deg, #96c121 0%, #c2d500 100%)" if is_final else "linear-gradient(135deg, #00829a 0%, #00a3b4 100%)"
        button_color = "linear-gradient(135deg, #96c121 0%, #c2d500 100%)" if is_final else "linear-gradient(135deg, #00829a 0%, #00a3b4 100%)"
        accent_color = "#96c121" if is_final else "#00829a"
        header_text = "✅ Aprobación Final" if is_final else "✅ Solicitud Aprobada"
        
        body_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8fafb; }}
                .header {{ background: {header_color}; color: white; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .header h2 {{ margin: 0; font-size: 24px; font-weight: bold; }}
                .content {{ background-color: white; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .detail {{ margin: 15px 0; padding: 10px; background-color: #f8fafb; border-radius: 4px; }}
                .detail strong {{ color: {accent_color}; font-weight: 600; }}
                .button {{ display: inline-block; padding: 14px 32px; background: {button_color}; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; box-shadow: 0 2px 4px rgba(0,130,154,0.3); }}
                .button:hover {{ opacity: 0.9; }}
                .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 12px; margin-top: 20px; }}
                .brand {{ color: #00829a; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{header_text}</h2>
                </div>
                <div class="content">
                    <p>Hola,</p>
                    <p>{'¡Tu solicitud ha sido aprobada exitosamente en todas las etapas!' if is_final else 'Tu solicitud ha avanzado a la siguiente etapa.'}</p>
                    
                    <div class="detail">
                        <strong>Solicitud:</strong> {solicitud_title}
                    </div>
                    <div class="detail">
                        <strong>ID:</strong> #{solicitud_id}
                    </div>
                    <div class="detail">
                        <strong>Etapa:</strong> {stage_name}
                    </div>
                    <div class="detail">
                        <strong>Aprobado por:</strong> {approver_name}
                    </div>
                    
                    <p style="margin-top: 30px; text-align: center;">
                        <a href="{solicitud_url}" class="button">Ver Solicitud</a>
                    </p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no responder.</p>
                    <p><span class="brand">CAFÉ QUINDÍO</span> - Sistema de Gestión de Marketing</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email([to_email], subject, body_html)
    
    def send_rejection_notification(
        self,
        to_email: str,
        solicitud_id: int,
        solicitud_title: str,
        comment: str,
        reviewer_name: str
    ) -> bool:
        """
        Enviar notificación de rechazo al creador
        
        Args:
            to_email: Correo del creador
            solicitud_id: ID de la solicitud
            solicitud_title: Título de la solicitud
            comment: Comentario del revisor
            reviewer_name: Nombre del revisor
            
        Returns:
            True si el correo se envió exitosamente
        """
        subject = f"Solicitud rechazada: {solicitud_title}"
        
        solicitud_url = f"{self.frontend_url}/solicitudes/{solicitud_id}"
        
        body_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8fafb; }}
                .header {{ background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .header h2 {{ margin: 0; font-size: 24px; font-weight: bold; }}
                .content {{ background-color: white; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .detail {{ margin: 15px 0; padding: 10px; background-color: #f8fafb; border-radius: 4px; }}
                .detail strong {{ color: #dc3545; font-weight: 600; }}
                .comment {{ background-color: #fff5f5; padding: 20px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 4px; }}
                .button {{ display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #00829a 0%, #00a3b4 100%); color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; box-shadow: 0 2px 4px rgba(0,130,154,0.3); }}
                .button:hover {{ opacity: 0.9; }}
                .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 12px; margin-top: 20px; }}
                .brand {{ color: #00829a; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>❌ Solicitud Rechazada</h2>
                </div>
                <div class="content">
                    <p>Hola,</p>
                    <p>Lamentamos informarte que tu solicitud ha sido rechazada:</p>
                    
                    <div class="detail">
                        <strong>Solicitud:</strong> {solicitud_title}
                    </div>
                    <div class="detail">
                        <strong>ID:</strong> #{solicitud_id}
                    </div>
                    <div class="detail">
                        <strong>Rechazado por:</strong> {reviewer_name}
                    </div>
                    
                    <div class="comment">
                        <strong style="color: #dc3545;">Motivo del rechazo:</strong>
                        <p style="margin: 10px 0 0 0;">{comment}</p>
                    </div>
                    
                    <p style="margin-top: 30px; text-align: center;">
                        <a href="{solicitud_url}" class="button">Ver Detalles</a>
                    </p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no responder.</p>
                    <p><span class="brand">CAFÉ QUINDÍO</span> - Sistema de Gestión de Marketing</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email([to_email], subject, body_html)


    def send_weekly_summary_email(
        self,
        recipient_email: str,
        recipient_name: str,
        solicitudes: list,
    ) -> bool:
        """
        Envía el resumen semanal de artes pendientes de aprobación.
        
        Args:
            recipient_email: Correo del destinatario
            recipient_name: Nombre del destinatario
            solicitudes: Lista de objetos Solicitud pendientes
            
        Returns:
            True si el correo se envió exitosamente
        """
        # Construir filas de la tabla HTML
        filas_html = ""
        for s in solicitudes:
            dias_pendiente = (datetime.utcnow() - s.created_at).days
            alerta_style = "color: #c0392b; font-weight: bold;" if dias_pendiente > 7 else ""
            filas_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{s.title}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{s.area.nombre if s.area else 'N/A'}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{s.stage.label if s.stage else 'N/A'}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                    <span style="{alerta_style}">{dias_pendiente} día(s)</span>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                    <a href="{self.frontend_url}/solicitudes/{s.id}"
                       style="color: #00829a; text-decoration: none; font-weight: bold;">Ver arte</a>
                </td>
            </tr>
            """

        week_range = self._get_week_range()

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; padding: 20px; margin: 0;">
            <div style="max-width: 700px; margin: 0 auto; background: white;
                        border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

                <!-- Header -->
                <div style="background: linear-gradient(135deg, #00829a 0%, #00a3b4 100%); padding: 24px 32px;">
                    <h1 style="color: white; margin: 0; font-size: 22px;">
                        Resumen Semanal de Artes Pendientes
                    </h1>
                    <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0 0; font-size: 14px;">
                        Marketing CQ &middot; Semana del {week_range}
                    </p>
                </div>

                <!-- Body -->
                <div style="padding: 32px;">
                    <p style="color: #333; font-size: 15px;">
                        Hola <strong>{recipient_name}</strong>,
                    </p>
                    <p style="color: #555; font-size: 14px;">
                        Tienes <strong style="color: #00829a;">{len(solicitudes)}</strong>
                        arte(s) pendiente(s) de tu aprobación esta semana:
                    </p>

                    <!-- Tabla de solicitudes -->
                    <table style="width: 100%; border-collapse: collapse; margin-top: 16px;
                                  font-size: 13px; color: #333;">
                        <thead>
                            <tr style="background-color: #f0f9fb;">
                                <th style="padding: 10px; text-align: left; color: #00829a;">Título</th>
                                <th style="padding: 10px; text-align: left; color: #00829a;">Área</th>
                                <th style="padding: 10px; text-align: left; color: #00829a;">Etapa</th>
                                <th style="padding: 10px; text-align: left; color: #00829a;">Tiempo en espera</th>
                                <th style="padding: 10px; text-align: left; color: #00829a;">Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filas_html}
                        </tbody>
                    </table>

                    <!-- CTA -->
                    <div style="text-align: center; margin-top: 28px;">
                        <a href="{self.frontend_url}"
                           style="background-color: #96c121; color: white; padding: 12px 28px;
                                  border-radius: 6px; text-decoration: none; font-size: 14px;
                                  font-weight: bold; display: inline-block;">
                            Ir al Panel de Aprobaciones
                        </a>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background-color: #f9f9f9; padding: 16px 32px;
                            border-top: 1px solid #eee; text-align: center;">
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        Este correo es generado automáticamente &middot;
                        <span style="color: #00829a; font-weight: bold;">CAFÉ QUINDÍO</span> - Marketing CQ
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        subject = f"[Marketing CQ] Resumen semanal: {len(solicitudes)} arte(s) por aprobar"
        return self.send_email([recipient_email], subject, html_body)

    @staticmethod
    def _get_week_range() -> str:
        """Retorna el rango de la semana actual como string legible."""
        today = datetime.utcnow()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return f"{monday.strftime('%d/%m')} - {sunday.strftime('%d/%m/%Y')}"


    # ── Emails de Iniciativas ──────────────────────────────────────────────

    def send_iniciativa_pending_gg_email(
        self,
        to_emails: List[str],
        iniciativa_id: int,
        iniciativa_titulo: str,
        director_name: str,
        producto_propuesto: str,
    ) -> bool:
        """Notificar a Gerencia General que hay una iniciativa pendiente"""
        url = f"{self.frontend_url}/iniciativas/{iniciativa_id}"
        html_body = f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8"></head>
        <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
          <div style="max-width:600px;margin:32px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
            <div style="background:linear-gradient(135deg,#00829a,#006d82);padding:28px 32px;">
              <h1 style="color:#fff;margin:0;font-size:20px;">Nueva Iniciativa de Producto</h1>
              <p style="color:#b2e4ed;margin:8px 0 0;font-size:14px;">Pendiente de aprobación Gerencia General</p>
            </div>
            <div style="padding:28px 32px;">
              <p style="color:#333;">Hola,</p>
              <p style="color:#555;"><strong>{director_name}</strong> ha enviado una nueva iniciativa para su revisión:</p>
              <div style="background:#f8f9fa;border-left:4px solid #00829a;padding:16px;border-radius:4px;margin:16px 0;">
                <p style="margin:0 0 8px;font-weight:bold;color:#333;">{iniciativa_titulo}</p>
                <p style="margin:0;color:#555;font-size:14px;"><strong>Producto propuesto:</strong> {producto_propuesto}</p>
              </div>
              <div style="text-align:center;margin:24px 0;">
                <a href="{url}" style="background:#00829a;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:bold;display:inline-block;">
                  Ver Iniciativa y Aprobar
                </a>
              </div>
            </div>
            <div style="background:#f9f9f9;padding:16px 32px;border-top:1px solid #eee;text-align:center;">
              <p style="color:#999;font-size:12px;margin:0;">Marketing CQ &middot; <span style="color:#00829a;font-weight:bold;">CAFÉ QUINDÍO</span></p>
            </div>
          </div>
        </body></html>
        """
        return self.send_email(to_emails, f"[Marketing CQ] Nueva iniciativa pendiente: {iniciativa_titulo}", html_body)

    def send_iniciativa_aprobada_area4_email(
        self,
        to_emails: List[str],
        iniciativa_id: int,
        iniciativa_titulo: str,
        producto_propuesto: str,
        gg_name: str,
    ) -> bool:
        """Notificar al Área 4 que deben iniciar el prototipado"""
        url = f"{self.frontend_url}/iniciativas/{iniciativa_id}"
        html_body = f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8"></head>
        <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
          <div style="max-width:600px;margin:32px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
            <div style="background:linear-gradient(135deg,#96c121,#7aa01a);padding:28px 32px;">
              <h1 style="color:#fff;margin:0;font-size:20px;">Nuevo Prototipado Requerido</h1>
              <p style="color:#d8f0a0;margin:8px 0 0;font-size:14px;">Gerencia General aprobó una iniciativa</p>
            </div>
            <div style="padding:28px 32px;">
              <p style="color:#333;">Hola equipo de Bebidas y Pastelería,</p>
              <p style="color:#555;"><strong>{gg_name}</strong> aprobó la siguiente iniciativa. Deben crear el prototipado:</p>
              <div style="background:#f8f9fa;border-left:4px solid #96c121;padding:16px;border-radius:4px;margin:16px 0;">
                <p style="margin:0 0 8px;font-weight:bold;color:#333;">{iniciativa_titulo}</p>
                <p style="margin:0;color:#555;font-size:14px;"><strong>Producto a prototipado:</strong> {producto_propuesto}</p>
              </div>
              <div style="text-align:center;margin:24px 0;">
                <a href="{url}" style="background:#96c121;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:bold;display:inline-block;">
                  Ver Detalles e Iniciar Prototipado
                </a>
              </div>
            </div>
            <div style="background:#f9f9f9;padding:16px 32px;border-top:1px solid #eee;text-align:center;">
              <p style="color:#999;font-size:12px;margin:0;">Marketing CQ &middot; <span style="color:#00829a;font-weight:bold;">CAFÉ QUINDÍO</span></p>
            </div>
          </div>
        </body></html>
        """
        return self.send_email(to_emails, f"[Marketing CQ] Nuevo prototipado requerido: {iniciativa_titulo}", html_body)

    def send_dual_approval_luisa_email(
        self,
        to_email: str,
        iniciativa_id: int,
        iniciativa_titulo: str,
    ) -> bool:
        """Notificar a Luisa Ibañez que debe aprobar el prototipado"""
        url = f"{self.frontend_url}/iniciativas/{iniciativa_id}"
        html_body = f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8"></head>
        <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
          <div style="max-width:600px;margin:32px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
            <div style="background:linear-gradient(135deg,#00829a,#006d82);padding:28px 32px;">
              <h1 style="color:#fff;margin:0;font-size:20px;">Aprobación de Prototipado Requerida</h1>
              <p style="color:#b2e4ed;margin:8px 0 0;font-size:14px;">Control de Calidad</p>
            </div>
            <div style="padding:28px 32px;">
              <p style="color:#333;">Hola Luisa,</p>
              <p style="color:#555;">El prototipado de la siguiente iniciativa requiere tu aprobación para continuar a Junta Directiva:</p>
              <div style="background:#f8f9fa;border-left:4px solid #00829a;padding:16px;border-radius:4px;margin:16px 0;">
                <p style="margin:0;font-weight:bold;color:#333;">{iniciativa_titulo}</p>
              </div>
              <div style="text-align:center;margin:24px 0;">
                <a href="{url}" style="background:#00829a;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:bold;display:inline-block;">
                  Revisar y Aprobar
                </a>
              </div>
            </div>
            <div style="background:#f9f9f9;padding:16px 32px;border-top:1px solid #eee;text-align:center;">
              <p style="color:#999;font-size:12px;margin:0;">Marketing CQ &middot; <span style="color:#00829a;font-weight:bold;">CAFÉ QUINDÍO</span></p>
            </div>
          </div>
        </body></html>
        """
        return self.send_email([to_email], f"[Marketing CQ] Aprobación requerida: {iniciativa_titulo}", html_body)

    def send_magic_link_email(
        self,
        to_email: str,
        to_name: str,
        token: str,
        iniciativa_id: int,
        iniciativa_titulo: str,
        producto_propuesto: str,
    ) -> bool:
        """Enviar Magic Link al Gerente de Tiendas (sin necesidad de login)"""
        approve_url = f"{self.frontend_url}/aprobar/{token}?action=APROBADO"
        reject_url = f"{self.frontend_url}/aprobar/{token}?action=RECHAZADO"
        html_body = f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8"></head>
        <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
          <div style="max-width:600px;margin:32px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
            <div style="background:linear-gradient(135deg,#333,#555);padding:28px 32px;">
              <h1 style="color:#fff;margin:0;font-size:20px;">Aprobación de Prototipado</h1>
              <p style="color:#ccc;margin:8px 0 0;font-size:14px;">Solicitud de validación - Café Quindío</p>
            </div>
            <div style="padding:28px 32px;">
              <p style="color:#333;">Hola {to_name},</p>
              <p style="color:#555;">Se requiere su validación para el siguiente prototipado de producto:</p>
              <div style="background:#f8f9fa;border-left:4px solid #96c121;padding:16px;border-radius:4px;margin:16px 0;">
                <p style="margin:0 0 8px;font-weight:bold;color:#333;">{iniciativa_titulo}</p>
                <p style="margin:0;color:#555;font-size:14px;"><strong>Producto:</strong> {producto_propuesto}</p>
              </div>
              <p style="color:#555;font-size:14px;">Por favor seleccione una de las siguientes opciones:</p>
              <div style="text-align:center;margin:24px 0;display:flex;gap:16px;justify-content:center;">
                <a href="{approve_url}"
                   style="background:#28a745;color:#fff;padding:14px 32px;border-radius:6px;text-decoration:none;font-size:15px;font-weight:bold;display:inline-block;margin-right:12px;">
                  ✓ APROBAR
                </a>
                <a href="{reject_url}"
                   style="background:#dc3545;color:#fff;padding:14px 32px;border-radius:6px;text-decoration:none;font-size:15px;font-weight:bold;display:inline-block;">
                  ✗ RECHAZAR
                </a>
              </div>
              <p style="color:#999;font-size:12px;text-align:center;">
                Este enlace es de uso único y expira en 72 horas.<br>
                No comparta este correo con terceros.
              </p>
            </div>
            <div style="background:#f9f9f9;padding:16px 32px;border-top:1px solid #eee;text-align:center;">
              <p style="color:#999;font-size:12px;margin:0;">Marketing CQ &middot; <span style="color:#00829a;font-weight:bold;">CAFÉ QUINDÍO</span></p>
            </div>
          </div>
        </body></html>
        """
        return self.send_email([to_email], f"[Café Quindío] Validación requerida: {iniciativa_titulo}", html_body)

    def send_jd_pending_email(
        self,
        to_emails: List[str],
        iniciativa_id: int,
        iniciativa_titulo: str,
    ) -> bool:
        """Notificar a Junta Directiva que una iniciativa está lista para aprobación final"""
        url = f"{self.frontend_url}/iniciativas/{iniciativa_id}"
        html_body = f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8"></head>
        <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
          <div style="max-width:600px;margin:32px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
            <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:28px 32px;">
              <h1 style="color:#fff;margin:0;font-size:20px;">Iniciativa Lista para Aprobación Final</h1>
              <p style="color:#aaa;margin:8px 0 0;font-size:14px;">Junta Directiva &middot; Café Quindío</p>
            </div>
            <div style="padding:28px 32px;">
              <p style="color:#333;">Estimada Junta Directiva,</p>
              <p style="color:#555;">La siguiente iniciativa ha completado el proceso de prototipado y validación. Requiere su aprobación final para proceder:</p>
              <div style="background:#f8f9fa;border-left:4px solid #96c121;padding:16px;border-radius:4px;margin:16px 0;">
                <p style="margin:0;font-weight:bold;color:#333;">{iniciativa_titulo}</p>
              </div>
              <div style="text-align:center;margin:24px 0;">
                <a href="{url}" style="background:#1a1a2e;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:bold;display:inline-block;">
                  Ver Iniciativa
                </a>
              </div>
            </div>
            <div style="background:#f9f9f9;padding:16px 32px;border-top:1px solid #eee;text-align:center;">
              <p style="color:#999;font-size:12px;margin:0;">Marketing CQ &middot; <span style="color:#00829a;font-weight:bold;">CAFÉ QUINDÍO</span></p>
            </div>
          </div>
        </body></html>
        """
        return self.send_email(to_emails, f"[Marketing CQ] Aprobación final requerida: {iniciativa_titulo}", html_body)


# Instancia global del servicio de email
email_service = EmailService()
