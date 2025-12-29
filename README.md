# YouTube Shorts Automation - Web App

Aplicación web para gestionar la automatización de subidas de YouTube Shorts.

## 🚀 Inicio rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

## 📖 Uso

### Primera configuración

1. **Conectar cuenta de Google**
   - Pega el contenido de tu `token.json` en la barra lateral
   - El token debe tener permisos para Drive, Sheets, YouTube y Gmail

2. **Configurar IDs**
   - ID de la carpeta `videos/` en Drive
   - ID de la carpeta `procesados/` en Drive
   - ID de la carpeta `errores/` en Drive
   - ID del Google Sheet
   - Nombre de la hoja (por defecto "Hoja 1")

### Funcionalidades

- **📤 Subir vídeo**: Sube vídeos directamente desde la web
- **📋 Cola de vídeos**: Edita títulos y descripciones de vídeos pendientes
- **📊 Historial**: Ve todos los Shorts subidos con enlaces a YouTube
- **🔧 Procesar ahora**: Fuerza el procesamiento inmediato

## 🌐 Desplegar en la nube

### Streamlit Cloud (Gratis)

1. Sube el código a un repositorio de GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu repositorio
4. Despliega

### Railway / Render

```bash
# railway.json o render.yaml
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.address 0.0.0.0"
  }
}
```

## 📁 Estructura del proyecto

```
youtube-shorts-app/
├── app.py              # Aplicación principal
├── requirements.txt    # Dependencias
└── README.md          # Este archivo
```

## 🔒 Seguridad

- El token se almacena solo en la sesión del navegador
- No se guarda ninguna credencial en el servidor
- Para producción, considera usar Streamlit Secrets o variables de entorno

## 📝 Notas

- Esta es una versión prototipo
- El procesamiento automático sigue dependiendo de la Cloud Function
- Para IA integrada, se necesitaría añadir llamadas a la API de Claude/OpenAI
