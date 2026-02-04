# RPA Playwright - Credito Digital + Core Financiero

Proyecto RPA code-first en Python para Windows (VM). Usa Playwright sync_api, configuracion por .env, logging robusto y evidencias por screenshots.

**Estructura**
- `bot/` codigo principal
- `runs/<timestamp>/` artefactos por ejecucion
- `requirements.txt` dependencias

**Requisitos**
- Windows 10/11 o Windows Server
- Python 3.10+
- Acceso a los portales web

**Instalacion (VS Code en Windows)**
1. Abrir la carpeta del proyecto en VS Code.
2. Crear y activar entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

4. Instalar navegador de Playwright:

```powershell
playwright install chromium
```

5. Crear archivo `.env` basado en `.env.example`.
6. Ejecutar el bot:

```powershell
python -m bot.main
```

**Archivos generados**
- `runs/<timestamp>/bot.log` logging completo
- `runs/<timestamp>/downloads/` archivo descargado
- `runs/<timestamp>/outputs/` archivo transformado
- `runs/<timestamp>/screenshots/` evidencias

**Configuracion (.env)**
Usa `.env.example` como plantilla. Los valores de campos para cada seccion se pasan como JSON.
Las claves del JSON deben coincidir con las claves en `CORE_SECTION1_FIELD_SELECTORS` y `CORE_SECTION2_FIELD_SELECTORS`.

Ejemplo:
- `CORE_SECTION1_FIELDS_JSON={"company":"001","period":"202501"}`
- `CORE_SECTION2_FIELDS_JSON={"company":"001","period":"202501"}`

**Dry Run**
- `DRY_RUN=true` llega hasta antes de "Contabilizar" y toma evidencia, pero no hace click.

**Headless**
- `HEADLESS=false` para ver el navegador.

**Selectores (IMPORTANTES)**
Los selectores en `bot/rpa/selectors.py` son placeholders. Debes reemplazarlos por los reales.

Como capturarlos con Playwright Inspector:
1. Ejecuta:

```powershell
playwright codegen https://tu-portal-url
```

2. Interactua con la pagina en la ventana de Inspector.
3. Copia los selectores y pegarlos en `bot/rpa/selectors.py`.

Nota: Asegurate de usar selectores estables (atributos data-testid, name, id).

**Errores comunes**
- Si falla la descarga o login, revisa `runs/<timestamp>/bot.log` y las capturas.
- Si no se detecta el separador, el archivo original se copia en `runs/<timestamp>/outputs/`.
