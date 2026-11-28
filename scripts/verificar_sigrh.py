from urllib.request import urlopen
from urllib.error import URLError, HTTPError

BASE = "http://127.0.0.1:8080"

RUTAS = [
    "/",
    "/salud/usuarios",
    "/salud/reclutamiento",
    "/salud/vacaciones",
    "/salud/nomina",
]


def main():
    errores = 0

    for ruta in RUTAS:
        direccion = BASE + ruta

        try:
            with urlopen(direccion, timeout=10) as respuesta:
                codigo = respuesta.status

            if codigo == 200:
                print(f"OK: {ruta} -> HTTP {codigo}")
            else:
                errores += 1
                print(f"ERROR: {ruta} -> HTTP {codigo}")

        except (URLError, HTTPError) as error:
            errores += 1
            print(f"ERROR: {ruta} -> {error}")

    if errores:
        raise SystemExit(
            f"Verificación incompleta: {errores} error(es)"
        )

    print("SIGRH responde correctamente")


if __name__ == "__main__":
    main()
