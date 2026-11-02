# SIGRH

Sistema para gestionar vacaciones, hecho con Django y SQLite. Incluye inicio de sesión, registro de empleados, consulta de días disponibles, solicitudes de vacaciones y su aprobación, rechazo o cancelación.

## Cómo ejecutar

Necesitas Python 3.12 o superior. Abre PowerShell en la carpeta del proyecto.

La primera vez, ejecuta:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py createsuperuser
```

Para iniciar el sistema:

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

Abre [http://127.0.0.1:8000/](http://127.0.0.1:8000/) e inicia sesión con el usuario y la contraseña que creaste. Desde **Administrar empleados** puedes agregar empleados.

Para detenerlo, presiona **Ctrl + C**.
