"""
Servicio de email usando Microsoft Graph API
"""
import logging
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


# Instancia global del servicio de email
email_service = EmailService()
