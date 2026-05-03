# app/api/services/email_service.py
"""
Servicio de envío de emails para notificaciones del sistema.
Gestiona el envío de emails mediante SMTP usando plantillas Jinja2.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import settings

# ── Configuración de Jinja2 ──
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "emails"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)


def _render_template(template_name: str, context: dict) -> str:
    """Renderiza una plantilla Jinja2 con el contexto dado."""
    template = jinja_env.get_template(template_name)
    return template.render(**context)


def _get_fecha_hora() -> tuple[str, str]:
    """Devuelve la fecha y hora actual formateadas en español."""
    now = datetime.now()
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    fecha = f"{now.day} de {meses[now.month - 1]} de {now.year}"
    hora = now.strftime("%H:%M")
    return fecha, hora


def enviar_email_recuperacion(
    email_destino: str,
    token: str,
    nombre_usuario: str,
) -> bool:
    """
    Envía un email de recuperación de contraseña al usuario.

    Args:
        email_destino: Email del usuario que solicita recuperación
        token: Token de recuperación generado
        nombre_usuario: Nombre del usuario para personalizar el email

    Returns:
        bool: True si el email se envió correctamente, False en caso contrario
    """
    url_recuperacion = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    fecha, hora = _get_fecha_hora()

    # Contexto para la plantilla
    context = {
        "nombre_usuario": nombre_usuario,
        "email": email_destino,
        "enlace_recuperacion": url_recuperacion,
        "minutos_expiracion": settings.RESET_TOKEN_EXPIRE_MINUTES,
        "fecha": fecha,
        "hora": hora,
        "fecha_solicitud": f"{fecha}, {hora}",
        "dispositivo": "Navegador web",
    }

    # Renderizar plantilla HTML
    html_content = _render_template("password_reset.html", context)

    # Texto plano como fallback
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

    # Verificar que SMTP esté configurado
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        print(f"[DEV] Email de recuperación para {email_destino}")
        print(f"[DEV] Token: {token}")
        print(f"[DEV] Enlace: {url_recuperacion}")
        return True

    try:
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = "Recuperación de contraseña - GoalApp"
        mensaje["From"] = settings.EMAIL_FROM
        mensaje["To"] = email_destino

        mensaje.attach(MIMEText(texto_plano, "plain"))
        mensaje.attach(MIMEText(html_content, "html"))

        if settings.SMTP_USE_SSL:
            # SSL puro (puerto 465)
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, email_destino, mensaje.as_string())
        else:
            # TLS (puerto 587)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, email_destino, mensaje.as_string())

        return True

    except Exception as e:
        print(f"Error enviando email de recuperación: {e}")
        return False


def enviar_email_invitacion(
    email_destino: str,
    nombre_invitado: str,
    liga_nombre: str,
    equipo_nombre: str,
    rol: str,
    dorsal: str,
    posicion: str,
    tipo_jugador: str,
    invitador_nombre: str,
    enlace_aceptar: str,
    fecha_invitacion: str | None = None,
) -> bool:
    """
    Envía un email de invitación a una liga.

    Args:
        email_destino: Email del usuario invitado
        nombre_invitado: Nombre del invitado
        liga_nombre: Nombre de la liga
        equipo_nombre: Nombre del equipo
        rol: Rol dentro de la liga
        dorsal: Número de dorsal
        posicion: Posición del jugador
        tipo_jugador: Tipo de jugador (titular, suplente, etc.)
        invitador_nombre: Nombre de quien invita
        enlace_aceptar: Enlace para aceptar la invitación
        fecha_invitacion: Fecha de la invitación (opcional)

    Returns:
        bool: True si el email se envió correctamente, False en caso contrario
    """
    fecha, hora = _get_fecha_hora()

    # Iniciales del invitador
    partes = invitador_nombre.strip().split()
    if len(partes) >= 2:
        invitador_iniciales = f"{partes[0][0]}{partes[-1][0]}".upper()
    else:
        invitador_iniciales = invitador_nombre[:2].upper()

    context = {
        "nombre_invitado": nombre_invitado,
        "liga_nombre": liga_nombre,
        "equipo_nombre": equipo_nombre,
        "rol": rol,
        "dorsal": dorsal,
        "posicion": posicion,
        "tipo_jugador": tipo_jugador,
        "invitador_nombre": invitador_nombre,
        "invitador_iniciales": invitador_iniciales,
        "enlace_aceptar": enlace_aceptar,
        "fecha": fecha,
        "hora": hora,
        "fecha_invitacion": fecha_invitacion or f"{fecha}, {hora}",
    }

    # Renderizar plantilla HTML
    html_content = _render_template("invitation.html", context)

    # Texto plano como fallback
    texto_plano = f"""
Hola {nombre_invitado},

Has sido invitado a formar parte de la liga "{liga_nombre}" en GoalApp.

Detalles:
- Liga: {liga_nombre}
- Equipo: {equipo_nombre}
- Rol: {rol}
- Dorsal: {dorsal}
- Posición: {posicion}

Para aceptar la invitación, visita el siguiente enlace:
{enlace_aceptar}

El enlace caduca en 7 días.

Saludos,
Equipo de GoalApp
    """

    # Verificar que SMTP esté configurado
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        print(f"[DEV] Email de invitación para {email_destino}")
        print(f"[DEV] Liga: {liga_nombre} | Equipo: {equipo_nombre}")
        print(f"[DEV] Enlace: {enlace_aceptar}")
        return True

    try:
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = f"Invitación a {liga_nombre} — GoalApp"
        mensaje["From"] = settings.EMAIL_FROM
        mensaje["To"] = email_destino

        mensaje.attach(MIMEText(texto_plano, "plain"))
        mensaje.attach(MIMEText(html_content, "html"))

        if settings.SMTP_USE_SSL:
            # SSL puro (puerto 465)
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, email_destino, mensaje.as_string())
        else:
            # TLS (puerto 587)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, email_destino, mensaje.as_string())

        return True

    except Exception as e:
        print(f"Error enviando email de invitación: {e}")
        return False