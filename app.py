"""
YouTube Shorts Automation - Web App v2
- Subida múltiple de vídeos
- Títulos opcionales (rellenar después)
- Procesamiento cuando el usuario decida
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

# Estilos CSS
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
    .upload-area {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 40px;
        text-align: center;
        background-color: #fafafa;
    }
    .video-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #1a73e8;
    }
    .status-pending {
        color: #856404;
        background-color: #fff3cd;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .status-ready {
        color: #0c5460;
        background-color: #d1ecf1;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .status-uploaded {
        color: #155724;
        background-color: #d4edda;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .status-error {
        color: #721c24;
        background-color: #f8d7da;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
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
    return build('drive', 'v3', credentials=credentials)


def get_sheets_service(credentials):
    return build('sheets', 'v4', credentials=credentials)


def get_youtube_service(credentials):
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
    """Actualizar título y descripción"""
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(file.getbuffer())
            tmp_path = tmp.name
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(tmp_path, resumable=True)
        
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
    """Sidebar con configuración"""
    with st.sidebar:
        st.markdown("## 🎬 YouTube Shorts")
        st.markdown("---")
        
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
                        st.success("✅ Conectado")
                        st.rerun()
                else:
                    st.warning("Pega el token JSON")
        
        if st.session_state.authenticated:
            st.success("✅ Autenticado")
            
            with st.expander("📁 Carpetas de Drive"):
                st.session_state.config['folder_videos'] = st.text_input(
                    "ID carpeta videos/",
                    value=st.session_state.config['folder_videos']
                )
                st.session_state.config['folder_procesados'] = st.text_input(
                    "ID carpeta procesados/",
                    value=st.session_state.config['folder_procesados']
                )
                st.session_state.config['folder_errores'] = st.text_input(
                    "ID carpeta errores/",
                    value=st.session_state.config['folder_errores']
                )
            
            with st.expander("📊 Google Sheet"):
                st.session_state.config['spreadsheet_id'] = st.text_input(
                    "ID del Spreadsheet",
                    value=st.session_state.config['spreadsheet_id']
                )
                st.session_state.config['sheet_name'] = st.text_input(
                    "Nombre de la hoja",
                    value=st.session_state.config['sheet_name']
                )
            
            with st.expander("📧 Notificaciones"):
                st.session_state.config['notification_email'] = st.text_input(
                    "Email",
                    value=st.session_state.config['notification_email']
                )
            
            st.markdown("---")
            if st.button("🚪 Desconectar"):
                st.session_state.authenticated = False
                st.session_state.credentials = None
                st.rerun()


def render_dashboard():
    """Dashboard principal"""
    st.markdown('<p class="main-header">🎬 YouTube Shorts Automation</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sube vídeos, rellena los datos cuando quieras, y procesa automáticamente</p>', unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        st.warning("👈 Conecta tu cuenta de Google en la barra lateral")
        render_instructions()
        return
    
    config = st.session_state.config
    if not config['folder_videos'] or not config['spreadsheet_id']:
        st.warning("⚙️ Configura los IDs de carpetas y Sheet en la barra lateral")
        return
    
    creds = st.session_state.credentials
    drive_service = get_drive_service(creds)
    sheets_service = get_sheets_service(creds)
    
    # Obtener datos
    df = get_sheet_data(sheets_service, config['spreadsheet_id'], config['sheet_name'])
    videos_in_drive = list_videos_in_folder(drive_service, config['folder_videos'])
    
    # Métricas
    render_metrics(df, videos_in_drive)
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Subir vídeos", 
        "✏️ Rellenar datos", 
        "📊 Historial",
        "🔄 Sincronizar"
    ])
    
    with tab1:
        render_upload_tab(drive_service, sheets_service, config)
    
    with tab2:
        render_edit_tab(sheets_service, config, df)
    
    with tab3:
        render_history_tab(df)
    
    with tab4:
        render_sync_tab(drive_service, sheets_service, config, df, videos_in_drive)


def render_instructions():
    """Instrucciones iniciales"""
    with st.expander("📖 ¿Cómo funciona?", expanded=True):
        st.markdown("""
        ### Flujo de trabajo
        
        1. **📤 Sube vídeos** → Arrastra uno o varios vídeos
        2. **⏳ Espera** → El sistema crea las filas automáticamente
        3. **✏️ Rellena datos** → Cuando quieras, añade título y descripción
        4. **🚀 Procesamiento** → La Cloud Function sube a YouTube los que tengan título
        
        ### Configuración necesaria
        
        1. Pega tu `token.json` en la barra lateral
        2. Configura los IDs de las carpetas de Drive
        3. Configura el ID del Google Sheet
        """)


def render_metrics(df, videos_in_drive):
    """Mostrar métricas"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📁 En Drive", len(videos_in_drive))
    
    with col2:
        pending = len(df[df['Estado'].str.contains('Pendiente', case=False, na=True) | (df['Estado'] == '')])
        st.metric("⏳ Sin título", pending)
    
    with col3:
        ready = len(df[(df['Título'].str.strip() != '') & (~df['Estado'].str.contains('Subido', case=False, na=False))])
        st.metric("✅ Listos", ready)
    
    with col4:
        uploaded = len(df[df['Estado'].str.contains('Subido', case=False, na=False)])
        st.metric("🎬 Subidos", uploaded)
    
    with col5:
        errors = len(df[df['Estado'].str.contains('Error', case=False, na=False)])
        st.metric("❌ Errores", errors)


def render_upload_tab(drive_service, sheets_service, config):
    """Tab de subida múltiple"""
    st.markdown("### 📤 Subir vídeos a Drive")
    st.info("💡 Sube los vídeos aquí. El sistema creará las filas en el Sheet automáticamente. Podrás rellenar título y descripción después.")
    
    uploaded_files = st.file_uploader(
        "Arrastra o selecciona vídeos (puedes subir varios)",
        type=['mp4', 'mov', 'avi'],
        accept_multiple_files=True,
        help="Formatos: MP4, MOV, AVI. Máximo 60 segundos para Shorts."
    )
    
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} vídeo(s) seleccionado(s)**")
        
        # Preview de vídeos
        cols = st.columns(min(len(uploaded_files), 3))
        for i, file in enumerate(uploaded_files):
            with cols[i % 3]:
                st.markdown(f"**{file.name}**")
                size_mb = file.size / (1024 * 1024)
                st.caption(f"{size_mb:.1f} MB")
        
        st.markdown("---")
        
        if st.button("🚀 Subir todos a Drive", type="primary"):
            progress = st.progress(0)
            status = st.empty()
            
            success_count = 0
            for i, file in enumerate(uploaded_files):
                status.text(f"Subiendo {file.name}...")
                
                result = upload_video_to_drive(
                    drive_service,
                    config['folder_videos'],
                    file,
                    file.name
                )
                
                if result:
                    # Añadir fila al Sheet con estado "Pendiente de rellenar"
                    row_data = [file.name, "", "", "Pendiente de rellenar", ""]
                    add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_data)
                    success_count += 1
                
                progress.progress((i + 1) / len(uploaded_files))
            
            status.empty()
            progress.empty()
            
            if success_count == len(uploaded_files):
                st.success(f"✅ {success_count} vídeo(s) subido(s) correctamente")
                st.balloons()
            else:
                st.warning(f"⚠️ {success_count}/{len(uploaded_files)} vídeos subidos")
            
            st.info("👉 Ve a la pestaña **'Rellenar datos'** para añadir títulos y descripciones")


def render_edit_tab(sheets_service, config, df):
    """Tab de edición de títulos y descripciones"""
    st.markdown("### ✏️ Rellenar títulos y descripciones")
    st.info("💡 Los vídeos con título relleno se procesarán automáticamente en el próximo ciclo (cada 5 minutos)")
    
    # Filtrar pendientes (sin título o con estado pendiente)
    pending_df = df[
        (df['Título'].str.strip() == '') | 
        (df['Estado'].str.contains('Pendiente', case=False, na=True)) |
        (df['Estado'] == '')
    ].copy()
    
    if pending_df.empty:
        st.success("🎉 No hay vídeos pendientes de rellenar")
        return
    
    st.markdown(f"**{len(pending_df)} vídeo(s) pendiente(s)**")
    
    # Formulario de edición
    for idx, row in pending_df.iterrows():
        with st.container():
            st.markdown(f"""
            <div class="video-card">
                <strong>📹 {row['Nombre archivo']}</strong>
                <span class="status-pending">Pendiente</span>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                new_titulo = st.text_input(
                    "Título",
                    value=row['Título'],
                    key=f"titulo_{idx}",
                    max_chars=100,
                    placeholder="Escribe el título del Short..."
                )
            
            with col2:
                new_descripcion = st.text_input(
                    "Descripción",
                    value=row['Descripción'],
                    key=f"desc_{idx}",
                    placeholder="Descripción (opcional)..."
                )
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Guardar", key=f"save_{idx}"):
                    row_num = idx + 2  # +2 por header y 0-index
                    if update_sheet_row(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_num, new_titulo, new_descripcion):
                        st.success("✅")
                        st.rerun()
            
            st.markdown("---")
    
    # Botón para guardar todos
    st.markdown("### Acciones rápidas")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Actualizar lista"):
            st.rerun()


def render_history_tab(df):
    """Tab de historial"""
    st.markdown("### 📊 Historial de subidas")
    
    # Filtrar subidos
    uploaded_df = df[df['Estado'].str.contains('Subido', case=False, na=False)].copy()
    
    if uploaded_df.empty:
        st.info("📭 No hay vídeos subidos todavía")
        return
    
    st.markdown(f"**{len(uploaded_df)} vídeo(s) subido(s) a YouTube**")
    
    for idx, row in uploaded_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"**{row['Título']}**")
                st.caption(f"📁 {row['Nombre archivo']}")
            
            with col2:
                desc = row['Descripción']
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                st.markdown(desc if desc else "*Sin descripción*")
            
            with col3:
                if row['YouTube URL']:
                    st.link_button("▶️ Ver", row['YouTube URL'])
            
            st.markdown("---")


def render_sync_tab(drive_service, sheets_service, config, df, videos_in_drive):
    """Tab de sincronización"""
    st.markdown("### 🔄 Sincronización")
    
    st.markdown("#### Vídeos en Drive sin registro en Sheet")
    
    # Encontrar vídeos en Drive que no están en el Sheet
    sheet_filenames = set(df['Nombre archivo'].str.lower())
    unregistered = [v for v in videos_in_drive if v['name'].lower() not in sheet_filenames]
    
    if unregistered:
        st.warning(f"⚠️ Hay {len(unregistered)} vídeo(s) en Drive sin entrada en el Sheet")
        
        for video in unregistered:
            col1, col2 = st.columns([3, 1])
            with col1:
                size_mb = int(video.get('size', 0)) / (1024 * 1024)
                st.markdown(f"📹 **{video['name']}** ({size_mb:.1f} MB)")
            with col2:
                if st.button("➕ Añadir", key=f"add_{video['id']}"):
                    row_data = [video['name'], "", "", "Pendiente de rellenar", ""]
                    if add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_data):
                        st.success("✅ Añadido")
                        st.rerun()
        
        st.markdown("---")
        
        if st.button("➕ Añadir todos al Sheet", type="primary"):
            for video in unregistered:
                row_data = [video['name'], "", "", "Pendiente de rellenar", ""]
                add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_data)
            st.success(f"✅ {len(unregistered)} vídeos añadidos")
            st.rerun()
    else:
        st.success("✅ Todos los vídeos están sincronizados")
    
    st.markdown("---")
    
    st.markdown("#### Estado del sistema")
    st.markdown(f"""
    - 📁 **Vídeos en Drive:** {len(videos_in_drive)}
    - 📊 **Filas en Sheet:** {len(df)}
    - ⏳ **Pendientes de título:** {len(df[(df['Título'].str.strip() == '') | (df['Estado'].str.contains('Pendiente', case=False, na=True))])}
    - ✅ **Listos para procesar:** {len(df[(df['Título'].str.strip() != '') & (~df['Estado'].str.contains('Subido', case=False, na=False)) & (~df['Estado'].str.contains('Error', case=False, na=False))])}
    """)
    
    st.markdown("---")
    
    st.markdown("#### Procesar manualmente")
    st.info("El sistema procesa automáticamente cada 5 minutos. Usa este botón para ver el estado o forzar el procesamiento.")
    
    if st.button("🔧 Ver logs de Cloud Function"):
        st.code("gcloud functions logs read youtube-shorts-uploader --region=europe-west1 --limit=20", language="bash")


def main():
    init_session_state()
    render_sidebar()
    render_dashboard()


if __name__ == "__main__":
    main()
