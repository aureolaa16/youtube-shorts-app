"""
YouTube Shorts Automation - Web App
Prototipo con Streamlit
"""

import streamlit as st
import pandas as pd
import json
import os
import tempfile
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Configuración de la página
st.set_page_config(
    page_title="YouTube Shorts Automation",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1a73e8;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-top: 0;
    }
    .status-pending {
        background-color: #fff3cd;
        padding: 5px 10px;
        border-radius: 5px;
        color: #856404;
    }
    .status-uploaded {
        background-color: #d4edda;
        padding: 5px 10px;
        border-radius: 5px;
        color: #155724;
    }
    .status-error {
        background-color: #f8d7da;
        padding: 5px 10px;
        border-radius: 5px;
        color: #721c24;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Inicializar estado de sesión"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'credentials' not in st.session_state:
        st.session_state.credentials = None
    if 'config' not in st.session_state:
        st.session_state.config = {
            'folder_videos': '',
            'folder_procesados': '',
            'folder_errores': '',
            'spreadsheet_id': '',
            'sheet_name': 'Hoja 1',
            'notification_email': ''
        }


def load_credentials_from_token(token_json):
    """Cargar credenciales desde JSON del token"""
    try:
        token_data = json.loads(token_json)
        credentials = Credentials.from_authorized_user_info(token_data)
        return credentials
    except Exception as e:
        st.error(f"Error cargando credenciales: {e}")
        return None


def get_drive_service(credentials):
    """Obtener servicio de Google Drive"""
    return build('drive', 'v3', credentials=credentials)


def get_sheets_service(credentials):
    """Obtener servicio de Google Sheets"""
    return build('sheets', 'v4', credentials=credentials)


def get_youtube_service(credentials):
    """Obtener servicio de YouTube"""
    return build('youtube', 'v3', credentials=credentials)


def list_videos_in_folder(drive_service, folder_id):
    """Listar vídeos en una carpeta de Drive"""
    try:
        query = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false"
        results = drive_service.files().list(
            q=query,
            fields="files(id, name, createdTime, size)",
            orderBy="createdTime desc"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        st.error(f"Error listando vídeos: {e}")
        return []


def get_sheet_data(sheets_service, spreadsheet_id, sheet_name):
    """Obtener datos del Sheet"""
    try:
        range_name = f"'{sheet_name}'!A:E"
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        rows = result.get('values', [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=['Nombre archivo', 'Título', 'Descripción', 'Estado', 'YouTube URL'])
        
        # Normalizar filas
        headers = ['Nombre archivo', 'Título', 'Descripción', 'Estado', 'YouTube URL']
        data = []
        for row in rows[1:]:
            while len(row) < 5:
                row.append('')
            data.append(row[:5])
        
        return pd.DataFrame(data, columns=headers)
    except Exception as e:
        st.error(f"Error obteniendo datos del Sheet: {e}")
        return pd.DataFrame(columns=['Nombre archivo', 'Título', 'Descripción', 'Estado', 'YouTube URL'])


def add_row_to_sheet(sheets_service, spreadsheet_id, sheet_name, row_data):
    """Añadir fila al Sheet"""
    try:
        range_name = f"'{sheet_name}'!A:E"
        sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row_data]}
        ).execute()
        return True
    except Exception as e:
        st.error(f"Error añadiendo fila: {e}")
        return False


def update_sheet_row(sheets_service, spreadsheet_id, sheet_name, row_num, titulo, descripcion):
    """Actualizar título y descripción de una fila"""
    try:
        range_name = f"'{sheet_name}'!B{row_num}:C{row_num}"
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body={"values": [[titulo, descripcion]]}
        ).execute()
        return True
    except Exception as e:
        st.error(f"Error actualizando fila: {e}")
        return False


def upload_video_to_drive(drive_service, folder_id, file, filename):
    """Subir vídeo a Google Drive"""
    try:
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp.write(file.getbuffer())
            tmp_path = tmp.name
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(tmp_path, mimetype='video/mp4', resumable=True)
        
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name'
        ).execute()
        
        os.unlink(tmp_path)
        return uploaded_file
    except Exception as e:
        st.error(f"Error subiendo vídeo: {e}")
        return None


def render_sidebar():
    """Renderizar sidebar con configuración"""
    with st.sidebar:
        st.image("https://www.gstatic.com/youtube/img/branding/youtubelogo/svg/youtubelogo.svg", width=150)
        st.markdown("### ⚙️ Configuración")
        
        # Autenticación
        with st.expander("🔐 Autenticación", expanded=not st.session_state.authenticated):
            token_input = st.text_area(
                "Pega el contenido de token.json",
                height=100,
                help="El token JSON generado con el script de autenticación"
            )
            
            if st.button("🔑 Conectar", type="primary"):
                if token_input:
                    creds = load_credentials_from_token(token_input)
                    if creds:
                        st.session_state.credentials = creds
                        st.session_state.authenticated = True
                        st.success("✅ Conectado correctamente")
                        st.rerun()
                else:
                    st.warning("Pega el token JSON")
        
        if st.session_state.authenticated:
            st.success("✅ Autenticado")
            
            # Configuración de IDs
            with st.expander("📁 Carpetas de Drive", expanded=False):
                st.session_state.config['folder_videos'] = st.text_input(
                    "ID carpeta videos/",
                    value=st.session_state.config['folder_videos'],
                    help="ID de la carpeta donde se suben los vídeos"
                )
                st.session_state.config['folder_procesados'] = st.text_input(
                    "ID carpeta procesados/",
                    value=st.session_state.config['folder_procesados']
                )
                st.session_state.config['folder_errores'] = st.text_input(
                    "ID carpeta errores/",
                    value=st.session_state.config['folder_errores']
                )
            
            with st.expander("📊 Google Sheet", expanded=False):
                st.session_state.config['spreadsheet_id'] = st.text_input(
                    "ID del Spreadsheet",
                    value=st.session_state.config['spreadsheet_id']
                )
                st.session_state.config['sheet_name'] = st.text_input(
                    "Nombre de la hoja",
                    value=st.session_state.config['sheet_name']
                )
            
            with st.expander("📧 Notificaciones", expanded=False):
                st.session_state.config['notification_email'] = st.text_input(
                    "Email para notificaciones",
                    value=st.session_state.config['notification_email']
                )
            
            st.divider()
            if st.button("🚪 Desconectar"):
                st.session_state.authenticated = False
                st.session_state.credentials = None
                st.rerun()


def render_dashboard():
    """Renderizar dashboard principal"""
    st.markdown('<p class="main-header">🎬 YouTube Shorts Automation</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gestiona y automatiza tus subidas de Shorts</p>', unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        st.warning("👈 Conecta tu cuenta de Google en la barra lateral para empezar")
        
        # Mostrar instrucciones
        with st.expander("📖 ¿Cómo empezar?", expanded=True):
            st.markdown("""
            ### Pasos para configurar:
            
            1. **Genera el token de autenticación** ejecutando el script Python con tus credenciales OAuth
            2. **Copia el contenido** del archivo `token.json` generado
            3. **Pégalo en la barra lateral** en la sección de Autenticación
            4. **Configura los IDs** de las carpetas de Drive y el Sheet
            
            ### Requisitos:
            - Proyecto en Google Cloud con las APIs habilitadas
            - Credenciales OAuth configuradas
            - Carpetas creadas en Google Drive
            - Google Sheet con las columnas correctas
            """)
        return
    
    # Verificar configuración
    config = st.session_state.config
    if not config['folder_videos'] or not config['spreadsheet_id']:
        st.warning("⚙️ Configura los IDs de carpetas y Sheet en la barra lateral")
        return
    
    # Obtener servicios
    creds = st.session_state.credentials
    drive_service = get_drive_service(creds)
    sheets_service = get_sheets_service(creds)
    
    # Métricas
    df = get_sheet_data(sheets_service, config['spreadsheet_id'], config['sheet_name'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = len(df)
        st.metric("📹 Total vídeos", total)
    
    with col2:
        pending = len(df[df['Estado'].str.contains('Pendiente', case=False, na=False)])
        st.metric("⏳ Pendientes", pending)
    
    with col3:
        uploaded = len(df[df['Estado'].str.contains('Subido', case=False, na=False)])
        st.metric("✅ Subidos", uploaded)
    
    with col4:
        errors = len(df[df['Estado'].str.contains('Error', case=False, na=False)])
        st.metric("❌ Errores", errors)
    
    st.divider()
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Subir vídeo", "📋 Cola de vídeos", "📊 Historial", "🔧 Procesar ahora"])
    
    with tab1:
        render_upload_tab(drive_service, sheets_service, config)
    
    with tab2:
        render_queue_tab(sheets_service, config, df)
    
    with tab3:
        render_history_tab(df)
    
    with tab4:
        render_process_tab(drive_service, sheets_service, config)


def render_upload_tab(drive_service, sheets_service, config):
    """Tab de subida de vídeos"""
    st.markdown("### 📤 Subir nuevo vídeo")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Arrastra o selecciona un vídeo",
            type=['mp4', 'mov', 'avi'],
            help="Formatos aceptados: MP4, MOV, AVI. Máximo 60 segundos para Shorts."
        )
        
        if uploaded_file:
            st.video(uploaded_file)
            
            file_size = uploaded_file.size / (1024 * 1024)
            st.caption(f"📁 {uploaded_file.name} ({file_size:.1f} MB)")
    
    with col2:
        st.markdown("#### Metadatos del Short")
        
        titulo = st.text_input(
            "Título",
            max_chars=100,
            help="Máximo 100 caracteres. Se añadirá #Shorts automáticamente."
        )
        
        descripcion = st.text_area(
            "Descripción",
            height=150,
            help="Puedes incluir hashtags y enlaces."
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            upload_now = st.checkbox("Subir y procesar inmediatamente", value=False)
        
        with col_btn2:
            if st.button("🚀 Subir vídeo", type="primary", disabled=not uploaded_file):
                if not titulo:
                    st.warning("Escribe un título para el vídeo")
                else:
                    with st.spinner("Subiendo vídeo a Google Drive..."):
                        result = upload_video_to_drive(
                            drive_service,
                            config['folder_videos'],
                            uploaded_file,
                            uploaded_file.name
                        )
                        
                        if result:
                            # Añadir fila al Sheet
                            row_data = [
                                uploaded_file.name,
                                titulo,
                                descripcion,
                                "Pendiente" if not upload_now else "En proceso",
                                ""
                            ]
                            
                            if add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_data):
                                st.success(f"✅ Vídeo '{uploaded_file.name}' subido correctamente")
                                st.balloons()
                            else:
                                st.error("Error añadiendo entrada al Sheet")


def render_queue_tab(sheets_service, config, df):
    """Tab de cola de vídeos"""
    st.markdown("### 📋 Cola de vídeos pendientes")
    
    # Filtrar pendientes
    pending_df = df[
        (df['Estado'].str.contains('Pendiente', case=False, na=True)) | 
        (df['Estado'] == '')
    ].copy()
    
    if pending_df.empty:
        st.info("🎉 No hay vídeos pendientes de procesar")
        return
    
    st.markdown(f"**{len(pending_df)} vídeo(s) en cola**")
    
    for idx, row in pending_df.iterrows():
        with st.expander(f"📹 {row['Nombre archivo']}", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                new_titulo = st.text_input(
                    "Título",
                    value=row['Título'],
                    key=f"titulo_{idx}",
                    max_chars=100
                )
                
                new_descripcion = st.text_area(
                    "Descripción",
                    value=row['Descripción'],
                    key=f"desc_{idx}",
                    height=100
                )
            
            with col2:
                st.markdown("**Estado actual:**")
                status = row['Estado'] if row['Estado'] else "Sin procesar"
                st.markdown(f"🔸 {status}")
                
                if st.button("💾 Guardar cambios", key=f"save_{idx}"):
                    # La fila en el Sheet es idx + 2 (header + 0-index)
                    row_num = idx + 2
                    if update_sheet_row(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_num, new_titulo, new_descripcion):
                        st.success("✅ Guardado")
                        st.rerun()


def render_history_tab(df):
    """Tab de historial"""
    st.markdown("### 📊 Historial de subidas")
    
    # Filtrar subidos
    uploaded_df = df[df['Estado'].str.contains('Subido', case=False, na=False)].copy()
    
    if uploaded_df.empty:
        st.info("📭 No hay vídeos subidos todavía")
        return
    
    st.markdown(f"**{len(uploaded_df)} vídeo(s) subido(s)**")
    
    for idx, row in uploaded_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"**{row['Título']}**")
                st.caption(row['Nombre archivo'])
            
            with col2:
                st.markdown(row['Descripción'][:100] + "..." if len(row['Descripción']) > 100 else row['Descripción'])
            
            with col3:
                if row['YouTube URL']:
                    st.link_button("▶️ Ver en YouTube", row['YouTube URL'])
            
            st.divider()


def render_process_tab(drive_service, sheets_service, config):
    """Tab de procesamiento manual"""
    st.markdown("### 🔧 Procesar vídeos manualmente")
    
    st.info("""
    El sistema procesa automáticamente cada 5 minutos. 
    Usa este botón si quieres forzar el procesamiento inmediato.
    """)
    
    # Mostrar vídeos en Drive
    st.markdown("#### Vídeos en carpeta /videos/")
    
    videos = list_videos_in_folder(drive_service, config['folder_videos'])
    
    if not videos:
        st.success("✅ No hay vídeos pendientes en Drive")
    else:
        for video in videos:
            col1, col2 = st.columns([3, 1])
            with col1:
                size_mb = int(video.get('size', 0)) / (1024 * 1024)
                st.markdown(f"📹 **{video['name']}** ({size_mb:.1f} MB)")
            with col2:
                created = video.get('createdTime', '')[:10]
                st.caption(created)
    
    st.divider()
    
    if st.button("⚡ Ejecutar procesamiento ahora", type="primary"):
        st.warning("⚠️ Esta función ejecutará el procesamiento completo. En el prototipo, esto requiere la Cloud Function desplegada.")
        st.code("curl https://europe-west1-PROJECT.cloudfunctions.net/youtube-shorts-uploader", language="bash")


def main():
    """Función principal"""
    init_session_state()
    render_sidebar()
    render_dashboard()


if __name__ == "__main__":
    main()
