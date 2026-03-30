# app/api/services/email_service.py
"""
Servicio de envío de emails para notificaciones del sistema.
Gestiona el envío de emails mediante SMTP para recuperación de contraseña
y otras notificaciones.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings


def enviar_email_recuperacion(
    email_destino: str,
    token: str,
    nombre_usuario: str
) -> bool:
    """
    Envía un email de recuperación de contraseña al usuario.

    Construye un email HTML con el enlace de recuperación y lo envía
    mediante el servidor SMTP configurado.

    Args:
        email_destino (str): Email del usuario que solicita recuperación
        token (str): Token de recuperación generado
        nombre_usuario (str): Nombre del usuario para personalizar el email

    Returns:
        bool: True si el email se envió correctamente, False en caso contrario
    """
    # Verificar que SMTP esté configurado
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        # En desarrollo, simular envío exitoso
        print(f"[DEV] Email de recuperación para {email_destino}")
        print(f"[DEV] Token: {token}")
        print(f"[DEV] Enlace: {settings.FRONTEND_URL}/reset-password?token={token}")
        return True

    try:
        # Construir el mensaje
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = "Recuperación de contraseña - GoalApp"
        mensaje["From"] = settings.EMAIL_FROM
        mensaje["To"] = email_destino

        # URL de recuperación
        url_recuperacion = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        # Contenido en texto plano
        texto_plano = f"""
Hola {nombre_usuario},

Has solicitado recuperar tu contraseña en GoalApp.

Para restablecer tu contraseña, visita el siguiente enlace:
{url_recuperacion}

Este enlace expirará en {settings.RESET_TOKEN_EXPIRE_MINUTES} minutos.

Si no has solicitado este cambio, puedes ignorar este email.

Saludos,
Equipo de GoalApp
        """

        # Contenido HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .button {{
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
        }}
        .footer {{ font-size: 12px; color: #666; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GoalApp</h1>
        </div>
        <div class="content">
            <p>Hola <strong>{nombre_usuario}</strong>,</p>
            <p>Has solicitado recuperar tu contraseña en GoalApp.</p>
            <p>Para restablecer tu contraseña, haz clic en el siguiente botón:</p>
            <p style="text-align: center;">
                <a href="{url_recuperacion}" class="button">Restablecer contraseña</a>
            </p>
            <p>Este enlace expirará en <strong>{settings.RESET_TOKEN_EXPIRE_MINUTES} minutos</strong>.</p>
            <p>Si no puedes hacer clic en el botón, copia y pega el siguiente enlace en tu navegador:</p>
            <p style="word-break: break-all; font-size: 12px;">{url_recuperacion}</p>
            <p>Si no has solicitado este cambio, puedes ignorar este email.</p>
        </div>
        <div class="footer">
            <p>Saludos,<br>Equipo de GoalApp</p>
        </div>
    </div>
</body>
</html>
        """

        # Adjuntar contenido
        mensaje.attach(MIMEText(texto_plano, "plain"))
        mensaje.attach(MIMEText(html, "html"))

        # Conectar al servidor SMTP y enviar
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, email_destino, mensaje.as_string())

        return True

    except Exception as e:
        print(f"Error enviando email de recuperación: {e}")
        return False