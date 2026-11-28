import json
import logging
import os
import time

from datetime import date
from uuid import UUID

import django
import pika

from django.db import (
    close_old_connections,
    transaction,
)


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

django.setup()

from nomina.models import VacacionAprobada


COLA = "nomina.vacaciones.aprobadas"
DLQ = "nomina.vacaciones.dlq"

REINTENTOS = [
    ("nomina.vacaciones.retry.5s", 5000),
    ("nomina.vacaciones.retry.15s", 15000),
    ("nomina.vacaciones.retry.45s", 45000),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger("consumidor")


def guardar_evento(mensaje):
    if mensaje.get("tipo") != "vacaciones.aprobadas":
        raise ValueError("Tipo de evento inesperado")

    datos = mensaje["datos"]

    evento_id = UUID(mensaje["id"])
    solicitud_id = int(datos["solicitud_id"])
    empleado_id = int(datos["empleado_id"])
    dias = int(datos["dias"])

    inicio = date.fromisoformat(
        datos["fecha_inicio"]
    )
    fin = date.fromisoformat(
        datos["fecha_fin"]
    )

    if (
        solicitud_id <= 0
        or empleado_id <= 0
        or dias <= 0
        or fin < inicio
    ):
        raise ValueError(
            "Datos de vacaciones inválidos"
        )

    # El identificador del evento es único.
    # Repetir el mensaje no duplica la novedad.
    with transaction.atomic():
        _, creado = (
            VacacionAprobada.objects.get_or_create(
                evento_id=evento_id,
                defaults={
                    "solicitud_id": solicitud_id,
                    "empleado_id": empleado_id,
                    "dias": dias,
                    "fecha_inicio": inicio,
                    "fecha_fin": fin,
                },
            )
        )

    return creado


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

            canal.queue_declare(
                queue=COLA,
                durable=True,
            )

            canal.queue_declare(
                queue=DLQ,
                durable=True,
            )

            # Las colas de reintento retienen los
            # mensajes durante el tiempo indicado.
            for nombre, espera_ms in REINTENTOS:
                canal.queue_declare(
                    queue=nombre,
                    durable=True,
                    arguments={
                        "x-message-ttl": espera_ms,
                        "x-dead-letter-exchange": "",
                        "x-dead-letter-routing-key": COLA,
                    },
                )

            canal.confirm_delivery()
            canal.basic_qos(prefetch_count=1)

            def recibir(
                canal,
                entrega,
                propiedades,
                cuerpo,
            ):
                close_old_connections()

                try:
                    mensaje = json.loads(
                        cuerpo.decode("utf-8")
                    )

                    creado = guardar_evento(mensaje)

                    logger.info(
                        "Evento %s",
                        (
                            "registrado"
                            if creado
                            else "duplicado ignorado"
                        ),
                    )

                    canal.basic_ack(
                        delivery_tag=entrega.delivery_tag
                    )
                    return

                except Exception as exc:
                    logger.exception(
                        "Error al procesar evento"
                    )

                    intento = int(
                        (propiedades.headers or {})
                        .get("intentos", 0)
                    )

                    if intento < 3:
                        destino = REINTENTOS[intento][0]
                    else:
                        destino = DLQ

                    cabeceras = {
                        "intentos": intento + 1,
                        "ultimo_error": str(exc)[:200],
                    }

                    try:
                        # Confirma el reenvío antes de
                        # reconocer el mensaje original.
                        canal.basic_publish(
                            exchange="",
                            routing_key=destino,
                            body=cuerpo,
                            mandatory=True,
                            properties=pika.BasicProperties(
                                content_type="application/json",
                                delivery_mode=2,
                                message_id=propiedades.message_id,
                                headers=cabeceras,
                            ),
                        )

                        canal.basic_ack(
                            delivery_tag=entrega.delivery_tag
                        )

                        logger.warning(
                            "Evento enviado a %s",
                            destino,
                        )

                    except Exception:
                        logger.exception(
                            "Falló el reenvío del evento"
                        )

                        canal.basic_nack(
                            delivery_tag=entrega.delivery_tag,
                            requeue=True,
                        )

            canal.basic_consume(
                queue=COLA,
                on_message_callback=recibir,
                auto_ack=False,
            )

            logger.info(
                "Consumidor de Nómina escuchando"
            )

            canal.start_consuming()

        except Exception:
            logger.exception(
                "Consumidor desconectado; reintentando"
            )
            time.sleep(5)

        finally:
            if conexion and conexion.is_open:
                conexion.close()


if __name__ == "__main__":
    ejecutar()
