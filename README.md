# descargar-preseea-con-selenium

Bot de [Selenium](https://www.selenium.dev/) que descarga automáticamente los archivos del
corpus **PRESEEA** (transcripciones y audios) desde la web del proyecto
([preseea.uah.es](https://preseea.uah.es/)).

El script abre el buscador del corpus en Chrome, lanza una búsqueda amplia, recorre la tabla
de resultados página a página y descarga los enlaces de cada entrada en una carpeta local
`downloads/`, usando `requests` con las *cookies* de la sesión del navegador.

## Requisitos

- Python 3.8 o superior.
- Google Chrome instalado. No hace falta descargar ChromeDriver a mano: con `selenium >= 4.6`,
  **Selenium Manager** lo resuelve automáticamente.
- Las dependencias de [`requirements.txt`](requirements.txt) (`selenium`, `requests`).

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
python download.py
```

Los archivos se guardan en la carpeta `downloads/` (se crea automáticamente). Si un archivo ya
existe, se omite, así que puedes reanudar la descarga volviendo a ejecutar el script. El
navegador se muestra por defecto; para ejecutarlo sin ventana, descomenta la línea
`--headless` en `download.py`.

## Notas

- Los selectores XPath dependen del HTML actual de `preseea.uah.es`; si la web cambia, puede que
  haya que actualizarlos.
- Usa el bot de forma responsable: descarga solo lo que necesites y evita sobrecargar el servidor
  del proyecto. Los datos del corpus pertenecen a **PRESEEA** (Universidad de Alcalá); revisa y
  respeta sus condiciones de uso y cita el corpus como corresponda.

## Licencia

[MIT](LICENSE) © Mateo Cámara.
