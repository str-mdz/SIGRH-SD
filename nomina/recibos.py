from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .cliente_api import ErrorServicio, catalogo_empleados, nomina_api


def _buscar_por_id(items, uid):
    for item in items:
        try:
            if int(item.get("id", 0)) == uid:
                return item
        except (TypeError, ValueError):
            continue
    return None


@login_required
@require_GET
def descargar(request, nomina_id):
    try:
        empleados = catalogo_empleados()
        actor = _buscar_por_id(empleados, request.user.pk)

        # La sesion web esta en SQLite; cotejamos identidad con Usuarios.
        if actor is None or actor.get("username") != request.user.get_username():
            raise PermissionDenied("Identidad no coincidente")

        respuesta = nomina_api(
            "GET", "nominas/", parametros={"actor_id": request.user.pk}
        )
        registros = respuesta.get("nominas")
        if not isinstance(registros, list):
            return HttpResponse("Respuesta de Nomina invalida", status=502)

        nomina = _buscar_por_id(registros, nomina_id)
        if nomina is None:
            raise Http404("Recibo no encontrado")

        empleado = _buscar_por_id(empleados, int(nomina["empleado_id"]))
    except ErrorServicio:
        return HttpResponse("Nomina o Usuarios no disponible", status=503)
    except (ValueError, TypeError, KeyError):
        return HttpResponse("Respuesta de Nomina invalida", status=502)

    buffer = BytesIO()
    documento = canvas.Canvas(buffer, pagesize=A4)
    documento.setTitle(f"Recibo SIGRH {nomina_id}")

    documento.setFont("Helvetica-Bold", 17)
    documento.drawString(55, 785, "SIGRH - Recibo de nomina")
    documento.setFont("Helvetica", 10)
    nombre = " ".join(
        x for x in (
            (empleado or {}).get("nombre", ""),
            (empleado or {}).get("apellido", ""),
        ) if x
    ) or (empleado or {}).get("username", f"ID {nomina['empleado_id']}")
    documento.drawString(55, 750, f"Empleado: {str(nombre)[:75]}")
    documento.drawString(55, 732, f"Periodo: {str(nomina['periodo'])[:75]}")
    documento.drawString(55, 714, f"Folio: {nomina_id}")

    filas = [
        ("Sueldo base", "sueldo_base"),
        ("Bono", "bono"),
        ("Descuento", "descuento"),
        ("Total a recibir", "total"),
    ]
    y = 675
    for etiqueta, campo in filas:
        documento.setFont(
            "Helvetica-Bold" if campo == "total" else "Helvetica", 11
        )
        documento.drawString(55, y, etiqueta)
        documento.drawRightString(535, y, f"$ {nomina[campo]} MXN")
        y -= 29

    documento.setFont("Helvetica", 9)
    documento.drawString(
        55, 80, "Documento informativo. No sustituye un CFDI de nomina."
    )
    documento.showPage()
    documento.save()

    respuesta_pdf = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    respuesta_pdf["Content-Disposition"] = (
        f'attachment; filename="recibo_nomina_{nomina_id}.pdf"'
    )
    respuesta_pdf["Cache-Control"] = "private, no-store"
    return respuesta_pdf
