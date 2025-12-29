"""
YouTube Shorts Automation - Web App v3
- Configuración persistente con Streamlit Secrets
- Subida múltiple de vídeos
- Títulos opcionales (rellenar después)
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
    initial_sidebar_state="collapsed"
)

# ============== CONFIGURACIÓN DESDE SECRETS ==============
# Estos valores se configuran una vez en Streamlit Cloud

def get_config():
    """Obtener configuración desde secrets o valores por defecto"""
    try:
        return {
            'folder_videos': st.secrets["google"]["folder_videos"],
            'folder_procesados': st.secrets["google"]["folder_procesados"],
            'folder_errores': st.secrets["google"]["folder_errores"],
            'spreadsheet_id': st.secrets["google"]["spreadsheet_id"],
            'sheet_name': st.secrets["google"]["sheet_name"],
            'notification_email': st.secrets["google"]["notification_email"],
        }
    except:
        return None

def get_credentials():
    """Obtener credenciales desde secrets"""
    try:
        token_data = {
            "token": st.secrets["google"]["token"],
            "refresh_token": st.secrets["google"]["refresh_token"],
            "token_uri": st.secrets["google"]["token_uri"],
            "client_id": st.secrets["google"]["client_id"],
            "client_secret": st.secrets["google"]["client_secret"],
            "scopes": st.secrets["google"]["scopes"]
        }
        return Credentials.from_authorized_user_info(token_data)
    except:
        return None

# ============== ESTILOS ==============
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
        margin-bottom: 20px;
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
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


# ============== SERVICIOS DE GOOGLE ==============

def get_drive_service(credentials):
    return build('drive', 'v3', credentials=credentials)

def get_sheets_service(credentials):
    return build('sheets', 'v4', credentials=credentials)

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


# ============== COMPONENTES UI ==============

def render_metrics(df, videos_in_drive):
    """Mostrar métricas en cards"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📁 En Drive", len(videos_in_drive))
    
    with col2:
        pending = len(df[(df['Título'].str.strip() == '') | (df['Estado'].str.contains('Pendiente', case=False, na=True))])
        st.metric("⏳ Sin título", pending)
    
    with col3:
        ready = len(df[(df['Título'].str.strip() != '') & (~df['Estado'].str.contains('Subido', case=False, na=False)) & (~df['Estado'].str.contains('Error', case=False, na=False))])
        st.metric("✅ Listos", ready)
    
    with col4:
        uploaded = len(df[df['Estado'].str.contains('Subido', case=False, na=False)])
        st.metric("🎬 Subidos", uploaded)
    
    with col5:
        errors = len(df[df['Estado'].str.contains('Error', case=False, na=False)])
        st.metric("❌ Errores", errors)


def render_upload_tab(drive_service, sheets_service, config):
    """Tab de subida múltiple"""
    st.markdown("### 📤 Subir vídeos")
    st.info("💡 Sube vídeos a Drive. Podrás rellenar título y descripción después en la pestaña 'Rellenar datos'.")
    
    uploaded_files = st.file_uploader(
        "Arrastra o selecciona vídeos",
        type=['mp4', 'mov', 'avi'],
        accept_multiple_files=True,
        help="Formatos: MP4, MOV, AVI. Máximo 60 segundos para Shorts."
    )
    
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} vídeo(s) seleccionado(s)**")
        
        # Preview
        for file in uploaded_files:
            size_mb = file.size / (1024 * 1024)
            st.markdown(f"- 📹 **{file.name}** ({size_mb:.1f} MB)")
        
        st.markdown("---")
        
        if st.button("🚀 Subir todos a Drive", type="primary", use_container_width=True):
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
                    row_data = [file.name, "", "", "Pendiente de rellenar", ""]
                    add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_data)
                    success_count += 1
                
                progress.progress((i + 1) / len(uploaded_files))
            
            status.empty()
            progress.empty()
            
            if success_count == len(uploaded_files):
                st.success(f"✅ {success_count} vídeo(s) subido(s)")
                st.balloons()
            else:
                st.warning(f"⚠️ {success_count}/{len(uploaded_files)} vídeos subidos")


def render_edit_tab(sheets_service, config, df):
    """Tab de edición de títulos"""
    st.markdown("### ✏️ Rellenar títulos y descripciones")
    st.info("💡 Los vídeos con título se procesarán automáticamente cada 5 minutos")
    
    # Filtrar pendientes
    pending_df = df[
        (df['Título'].str.strip() == '') | 
        (df['Estado'].str.contains('Pendiente', case=False, na=True)) |
        (df['Estado'] == '')
    ].copy()
    
    if pending_df.empty:
        st.success("🎉 No hay vídeos pendientes")
        return
    
    st.markdown(f"**{len(pending_df)} vídeo(s) pendiente(s)**")
    st.markdown("---")
    
    for idx, row in pending_df.iterrows():
        with st.container():
            st.markdown(f"📹 **{row['Nombre archivo']}**")
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                new_titulo = st.text_input(
                    "Título",
                    value=row['Título'],
                    key=f"titulo_{idx}",
                    max_chars=100,
                    label_visibility="collapsed",
                    placeholder="Título del Short..."
                )
            
            with col2:
                new_descripcion = st.text_input(
                    "Descripción",
                    value=row['Descripción'],
                    key=f"desc_{idx}",
                    label_visibility="collapsed",
                    placeholder="Descripción..."
                )
            
            with col3:
                if st.button("💾 Guardar", key=f"save_{idx}", use_container_width=True):
                    row_num = idx + 2
                    if update_sheet_row(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_num, new_titulo, new_descripcion):
                        st.success("✅")
                        st.rerun()
            
            st.markdown("---")


def render_history_tab(df):
    """Tab de historial"""
    st.markdown("### 📊 Vídeos subidos a YouTube")
    
    uploaded_df = df[df['Estado'].str.contains('Subido', case=False, na=False)].copy()
    
    if uploaded_df.empty:
        st.info("📭 No hay vídeos subidos todavía")
        return
    
    st.markdown(f"**{len(uploaded_df)} Short(s) en YouTube**")
    st.markdown("---")
    
    for idx, row in uploaded_df.iterrows():
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown(f"**{row['Título']}**")
            st.caption(row['Nombre archivo'])
        
        with col2:
            desc = row['Descripción'][:60] + "..." if len(row['Descripción']) > 60 else row['Descripción']
            st.markdown(desc if desc else "*Sin descripción*")
        
        with col3:
            if row['YouTube URL']:
                st.link_button("▶️ Ver", row['YouTube URL'], use_container_width=True)
        
        st.markdown("---")


def render_sync_tab(drive_service, sheets_service, config, df, videos_in_drive):
    """Tab de sincronización"""
    st.markdown("### 🔄 Sincronización")
    
    # Vídeos sin registro
    sheet_filenames = set(df['Nombre archivo'].str.lower())
    unregistered = [v for v in videos_in_drive if v['name'].lower() not in sheet_filenames]
    
    if unregistered:
        st.warning(f"⚠️ {len(unregistered)} vídeo(s) en Drive sin registro")
        
        for video in unregistered:
            col1, col2 = st.columns([3, 1])
            with col1:
                size_mb = int(video.get('size', 0)) / (1024 * 1024)
                st.markdown(f"📹 **{video['name']}** ({size_mb:.1f} MB)")
            with col2:
                if st.button("➕ Añadir", key=f"add_{video['id']}"):
                    row_data = [video['name'], "", "", "Pendiente de rellenar", ""]
                    if add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_data):
                        st.rerun()
        
        st.markdown("---")
        if st.button("➕ Añadir todos", type="primary"):
            for video in unregistered:
                row_data = [video['name'], "", "", "Pendiente de rellenar", ""]
                add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_data)
            st.success(f"✅ {len(unregistered)} añadidos")
            st.rerun()
    else:
        st.success("✅ Todo sincronizado")
    
    st.markdown("---")
    st.markdown("#### 📊 Estado")
    st.markdown(f"""
    - **En Drive:** {len(videos_in_drive)}
    - **En Sheet:** {len(df)}
    - **Pendientes:** {len(df[df['Título'].str.strip() == ''])}
    - **Subidos:** {len(df[df['Estado'].str.contains('Subido', case=False, na=False)])}
    """)


def render_setup_instructions():
    """Mostrar instrucciones de configuración"""
    st.markdown('<p class="main-header">🎬 YouTube Shorts Automation</p>', unsafe_allow_html=True)
    
    st.error("⚠️ Configuración no encontrada")
    
    st.markdown("""
    ### Configuración inicial
    
    Para que la app funcione, necesitas configurar los **Secrets** en Streamlit Cloud:
    
    1. Ve a tu app en [share.streamlit.io](https://share.streamlit.io)
    2. Clic en **Settings** (⚙️) → **Secrets**
    3. Pega la siguiente configuración (reemplaza los valores):
    """)
    
    st.code("""
[google]
# IDs de carpetas de Drive
folder_videos = "TU_ID_CARPETA_VIDEOS"
folder_procesados = "TU_ID_CARPETA_PROCESADOS"
folder_errores = "TU_ID_CARPETA_ERRORES"

# Google Sheet
spreadsheet_id = "TU_ID_SPREADSHEET"
sheet_name = "Hoja 1"

# Notificaciones
notification_email = "tu@email.com"

# Token OAuth (copia estos valores de tu token.json)
token = "ya29.xxxxx"
refresh_token = "1//xxxxx"
token_uri = "https://oauth2.googleapis.com/token"
client_id = "xxxxx.apps.googleusercontent.com"
client_secret = "GOCSPX-xxxxx"
scopes = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/gmail.send"]
    """, language="toml")
    
    st.markdown("""
    4. Clic en **Save**
    5. La app se reiniciará automáticamente
    
    ---
    
    ### ¿Dónde encuentro estos valores?
    
    | Campo | Dónde encontrarlo |
    |-------|-------------------|
    | `folder_videos` | URL de la carpeta en Drive → el ID es la parte después de `/folders/` |
    | `spreadsheet_id` | URL del Sheet → el ID es la parte después de `/d/` |
    | `token`, `refresh_token`, etc. | Dentro de tu archivo `token.json` |
    """)


def main():
    """Función principal"""
    
    # Obtener configuración
    config = get_config()
    credentials = get_credentials()
    
    # Si no hay configuración, mostrar instrucciones
    if not config or not credentials:
        render_setup_instructions()
        return
    
    # Header
    st.markdown('<p class="main-header">🎬 YouTube Shorts Automation</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sube vídeos, rellena datos cuando quieras, procesamiento automático</p>', unsafe_allow_html=True)
    
    # Servicios
    drive_service = get_drive_service(credentials)
    sheets_service = get_sheets_service(credentials)
    
    # Datos
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
    
    # Footer
    st.markdown("---")
    st.caption(f"📧 Notificaciones a: {config['notification_email']} | ⏱️ Procesamiento automático cada 5 min")


if __name__ == "__main__":
    main()
