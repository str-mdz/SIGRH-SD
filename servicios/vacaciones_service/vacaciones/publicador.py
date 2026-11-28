import logging
import os
import time
import json
import django
import pika

from django.db import close_old_connections
from django.utils import timezone


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

django.setup()

from vacaciones.models import EventoSalida


COLA = "nomina.vacaciones.aprobadas"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger("publicador")


def abrir_conexion():
    credenciales = pika.PlainCredentials(
        os.environ["RABBITMQ_USER"],
        os.environ["RABBITMQ_PASSWORD"],
    )

    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv(
                "RABBITMQ_HOST",
                "rabbitmq",
            ),
            credentials=credenciales,
            heartbeat=60,
            blocked_connection_timeout=10,
            socket_timeout=5,
        )
    )


def ejecutar():
    while True:
        conexion = None

        try:
            conexion = abrir_conexion()
            canal = conexion.channel()

            # La cola sobrevivirá a reinicios del broker.
            canal.queue_declare(
                queue=COLA,
                durable=True,
            )

            # Espera confirmaciones de RabbitMQ.
            canal.confirm_delivery()

            logger.info(
                "Publicador conectado a RabbitMQ"
            )

            while True:
                close_old_connections()

                pendientes = (
                    EventoSalida.objects
                    .filter(publicado=False)
                    .order_by("fecha_creacion")[:20]
                )

                for evento in pendientes:
                    mensaje = {
                        "id": str(evento.pk),
                        "tipo": evento.tipo,
                        "datos": evento.datos,
                    }

                    cuerpo = json.dumps(
                        mensaje,
                        ensure_ascii=False,
                    ).encode("utf-8")

                    # Publica antes de marcar el evento.
                    canal.basic_publish(
                        exchange="",
                        routing_key=COLA,
                        body=cuerpo,
                        mandatory=True,
                        properties=pika.BasicProperties(
                            content_type="application/json",
                            delivery_mode=2,
                            message_id=str(evento.pk),
                        ),
                    )

                    EventoSalida.objects.filter(
                        pk=evento.pk,
                        publicado=False,
                    ).update(
                        publicado=True,
                        fecha_publicacion=timezone.now(),
                    )

                    logger.info(
                        "Evento publicado: %s",
                        evento.pk,
                    )

                time.sleep(2)

        except Exception:
            logger.exception(
                "Error de publicación; "
                "eventos conservados en Outbox"
            )
            time.sleep(5)

        finally:
            if conexion and conexion.is_open:
                conexion.close()


if __name__ == "__main__":
    ejecutar()
