"""
YouTube Shorts Automation - Web App v5
- Progreso detallado de subida
- Notificaciones visuales
- Estados en tiempo real
- Mejor UX
"""

import streamlit as st
import pandas as pd
import json
import os
import tempfile
import time
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

def get_config():
    """Obtener configuración desde secrets"""
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
    
    /* Cards de métricas */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    /* Estados */
    .status-uploading {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: 500;
        display: inline-block;
        animation: pulse 1.5s infinite;
    }
    .status-success {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: 500;
        display: inline-block;
    }
    .status-error {
        background-color: #ffebee;
        color: #c62828;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: 500;
        display: inline-block;
    }
    .status-pending {
        background-color: #fff8e1;
        color: #f57f17;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: 500;
        display: inline-block;
    }
    
    /* Animación pulse */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
    
    /* Progress container */
    .upload-progress-container {
        background-color: #f5f5f5;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid #e0e0e0;
    }
    .upload-item {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #1a73e8;
    }
    .upload-item-success {
        border-left-color: #4caf50;
    }
    .upload-item-error {
        border-left-color: #f44336;
    }
    
    /* Video card */
    .video-card {
        background-color: #fafafa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #eee;
        transition: all 0.2s;
    }
    .video-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* Toast notifications */
    .toast-success {
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #4caf50;
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    }
    .toast-error {
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #f44336;
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Tabs mejorados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f5f5f5;
        padding: 5px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Botones */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* File uploader */
    .uploadedFile {
        background-color: #e3f2fd;
        border-radius: 8px;
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
        return False

def upload_video_to_drive_with_progress(drive_service, folder_id, file, filename, progress_callback=None):
    """Subir vídeo a Google Drive con progreso"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(file.getbuffer())
            tmp_path = tmp.name
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        file_size = os.path.getsize(tmp_path)
        
        media = MediaFileUpload(
            tmp_path, 
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )
        
        request = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name'
        )
        
        response = None
        start_time = time.time()
        
        while response is None:
            status, response = request.next_chunk()
            if status and progress_callback:
                progress = status.progress()
                elapsed = time.time() - start_time
                speed = (progress * file_size) / elapsed if elapsed > 0 else 0
                progress_callback(progress, speed, elapsed)
        
        os.unlink(tmp_path)
        return response
    except Exception as e:
        st.error(f"Error: {e}")
        return None


# ============== COMPONENTES UI ==============

def render_metrics(df, videos_in_drive):
    """Métricas con diseño mejorado"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #42a5f5, #1e88e5); padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 2rem; font-weight: bold;">{len(videos_in_drive)}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">📁 En Drive</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pending = len(df[(df['Título'].str.strip() == '') | (df['Estado'].str.contains('Pendiente', case=False, na=True))])
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ffb74d, #ff9800); padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 2rem; font-weight: bold;">{pending}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">⏳ Sin título</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        ready = len(df[(df['Título'].str.strip() != '') & (~df['Estado'].str.contains('Subido', case=False, na=False)) & (~df['Estado'].str.contains('Error', case=False, na=False)) & (~df['Estado'].str.contains('Pendiente', case=False, na=True))])
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #66bb6a, #43a047); padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 2rem; font-weight: bold;">{ready}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">✅ Listos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        uploaded = len(df[df['Estado'].str.contains('Subido', case=False, na=False)])
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ab47bc, #8e24aa); padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 2rem; font-weight: bold;">{uploaded}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">🎬 Subidos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        errors = len(df[df['Estado'].str.contains('Error', case=False, na=False)])
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ef5350, #e53935); padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 2rem; font-weight: bold;">{errors}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">❌ Errores</div>
        </div>
        """, unsafe_allow_html=True)


def format_size(size_bytes):
    """Formatear tamaño en bytes a formato legible"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024*1024:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/(1024*1024):.1f} MB"


def format_speed(speed_bytes):
    """Formatear velocidad"""
    if speed_bytes < 1024:
        return f"{speed_bytes:.0f} B/s"
    elif speed_bytes < 1024*1024:
        return f"{speed_bytes/1024:.1f} KB/s"
    else:
        return f"{speed_bytes/(1024*1024):.1f} MB/s"


def render_upload_tab(drive_service, sheets_service, config):
    """Tab de subida con progreso mejorado"""
    st.markdown("### 📤 Subir vídeos")
    
    # Info box
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 4px solid #1976d2; margin-bottom: 20px;">
        <strong>💡 Consejo:</strong> Sube los vídeos aquí. Después podrás añadir título y descripción en la pestaña "Rellenar datos".
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Arrastra o selecciona vídeos",
        type=['mp4', 'mov', 'avi'],
        accept_multiple_files=True,
        help="Formatos: MP4, MOV, AVI. Máximo 60 segundos para Shorts."
    )
    
    if uploaded_files:
        # Resumen de archivos
        total_size = sum(f.size for f in uploaded_files)
        
        st.markdown(f"""
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 10px; margin: 15px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{len(uploaded_files)} vídeo(s) seleccionado(s)</strong>
                    <span style="color: #666; margin-left: 10px;">({format_size(total_size)} total)</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Lista de archivos
        for file in uploaded_files:
            st.markdown(f"""
            <div style="background-color: white; padding: 10px 15px; border-radius: 8px; margin: 5px 0; border: 1px solid #eee; display: flex; align-items: center;">
                <span style="font-size: 1.5rem; margin-right: 10px;">📹</span>
                <div>
                    <strong>{file.name}</strong>
                    <span style="color: #666; font-size: 0.85rem; margin-left: 10px;">{format_size(file.size)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        
        if st.button("🚀 Subir todos a Drive", type="primary", use_container_width=True):
            
            # Contenedor de progreso
            st.markdown("""
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <h4 style="margin-top: 0;">📤 Subiendo vídeos...</h4>
            </div>
            """, unsafe_allow_html=True)
            
            overall_progress = st.progress(0)
            
            results = []
            
            for i, file in enumerate(uploaded_files):
                # Status del archivo actual
                file_status = st.empty()
                file_progress = st.progress(0)
                file_details = st.empty()
                
                file_status.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #1976d2;">
                    <div style="display: flex; align-items: center;">
                        <div class="status-uploading" style="margin-right: 10px;">⏳ Subiendo...</div>
                        <strong>{file.name}</strong>
                        <span style="color: #666; margin-left: 10px;">({format_size(file.size)})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                def update_progress(progress, speed, elapsed):
                    file_progress.progress(progress)
                    remaining = ((1 - progress) * elapsed / progress) if progress > 0 else 0
                    file_details.markdown(f"""
                    <div style="display: flex; justify-content: space-between; color: #666; font-size: 0.85rem; padding: 0 5px;">
                        <span>⚡ {format_speed(speed)}</span>
                        <span>⏱️ {remaining:.0f}s restantes</span>
                        <span>📊 {progress*100:.0f}%</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Subir
                result = upload_video_to_drive_with_progress(
                    drive_service,
                    config['folder_videos'],
                    file,
                    file.name,
                    update_progress
                )
                
                if result:
                    # Añadir al Sheet
                    add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], 
                                    [file.name, "", "", "Pendiente de rellenar", ""])
                    
                    file_status.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #4caf50;">
                        <div style="display: flex; align-items: center;">
                            <div class="status-success" style="margin-right: 10px;">✅ Completado</div>
                            <strong>{file.name}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    file_progress.progress(100)
                    results.append(("success", file.name))
                else:
                    file_status.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #f44336;">
                        <div style="display: flex; align-items: center;">
                            <div class="status-error" style="margin-right: 10px;">❌ Error</div>
                            <strong>{file.name}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    results.append(("error", file.name))
                
                file_details.empty()
                overall_progress.progress((i + 1) / len(uploaded_files))
            
            # Resumen final
            success_count = len([r for r in results if r[0] == "success"])
            error_count = len([r for r in results if r[0] == "error"])
            
            st.markdown("---")
            
            if error_count == 0:
                st.success(f"🎉 ¡{success_count} vídeo(s) subido(s) correctamente!")
                st.balloons()
                st.info("👉 Ve a la pestaña **'✏️ Rellenar datos'** para añadir títulos y descripciones")
            else:
                st.warning(f"⚠️ {success_count} subido(s), {error_count} con error")


def render_edit_tab(sheets_service, config, df):
    """Tab de edición mejorado"""
    st.markdown("### ✏️ Rellenar títulos y descripciones")
    
    st.markdown("""
    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 4px solid #4caf50; margin-bottom: 20px;">
        <strong>💡 Info:</strong> Los vídeos con título se procesarán automáticamente cada 5 minutos y se subirán a YouTube.
    </div>
    """, unsafe_allow_html=True)
    
    # Filtrar pendientes
    pending_df = df[
        (df['Título'].str.strip() == '') | 
        (df['Estado'].str.contains('Pendiente', case=False, na=True)) |
        (df['Estado'] == '')
    ].copy()
    
    if pending_df.empty:
        st.markdown("""
        <div style="background-color: #f5f5f5; padding: 40px; border-radius: 10px; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 10px;">🎉</div>
            <div style="font-size: 1.2rem; color: #666;">No hay vídeos pendientes de rellenar</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"**{len(pending_df)} vídeo(s) pendiente(s)**")
    
    for idx, row in pending_df.iterrows():
        with st.container():
            st.markdown(f"""
            <div class="video-card">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 1.5rem; margin-right: 10px;">📹</span>
                    <strong>{row['Nombre archivo']}</strong>
                    <span class="status-pending" style="margin-left: 15px;">Pendiente</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                new_titulo = st.text_input(
                    "Título",
                    value=row['Título'],
                    key=f"titulo_{idx}",
                    max_chars=100,
                    placeholder="✍️ Escribe el título del Short..."
                )
            
            with col2:
                new_descripcion = st.text_input(
                    "Descripción",
                    value=row['Descripción'],
                    key=f"desc_{idx}",
                    placeholder="📝 Descripción (opcional)..."
                )
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Guardar", key=f"save_{idx}", use_container_width=True):
                    if new_titulo.strip():
                        row_num = idx + 2
                        if update_sheet_row(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_num, new_titulo, new_descripcion):
                            st.toast(f"✅ '{new_titulo}' guardado correctamente", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.toast("⚠️ El título no puede estar vacío", icon="⚠️")
            
            st.markdown("---")


def render_history_tab(df):
    """Tab de historial mejorado"""
    st.markdown("### 📊 Vídeos subidos a YouTube")
    
    uploaded_df = df[df['Estado'].str.contains('Subido', case=False, na=False)].copy()
    
    if uploaded_df.empty:
        st.markdown("""
        <div style="background-color: #f5f5f5; padding: 40px; border-radius: 10px; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 10px;">📭</div>
            <div style="font-size: 1.2rem; color: #666;">No hay vídeos subidos todavía</div>
            <div style="font-size: 0.9rem; color: #999; margin-top: 10px;">Los vídeos aparecerán aquí cuando se suban a YouTube</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"""
    <div style="background-color: #f3e5f5; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <strong>🎬 {len(uploaded_df)} Short(s) en YouTube</strong>
    </div>
    """, unsafe_allow_html=True)
    
    for idx, row in uploaded_df.iterrows():
        st.markdown(f"""
        <div class="video-card" style="border-left: 4px solid #9c27b0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="font-size: 1.1rem;">{row['Título']}</strong>
                    <div style="color: #666; font-size: 0.85rem; margin-top: 5px;">📁 {row['Nombre archivo']}</div>
                    <div style="color: #888; font-size: 0.85rem; margin-top: 3px;">{row['Descripción'][:80] + '...' if len(row['Descripción']) > 80 else row['Descripción']}</div>
                </div>
                <div class="status-success">✅ Subido</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if row['YouTube URL']:
            st.link_button("▶️ Ver en YouTube", row['YouTube URL'], use_container_width=False)
        
        st.markdown("")


def render_sync_tab(drive_service, sheets_service, config, df, videos_in_drive):
    """Tab de sincronización mejorado"""
    st.markdown("### 🔄 Sincronización")
    
    sheet_filenames = set(df['Nombre archivo'].str.lower())
    unregistered = [v for v in videos_in_drive if v['name'].lower() not in sheet_filenames]
    
    if unregistered:
        st.markdown(f"""
        <div style="background-color: #fff3e0; padding: 15px; border-radius: 10px; border-left: 4px solid #ff9800; margin-bottom: 20px;">
            <strong>⚠️ {len(unregistered)} vídeo(s) en Drive sin registro en el Sheet</strong>
            <div style="color: #666; font-size: 0.9rem; margin-top: 5px;">Estos vídeos están en Drive pero no aparecen en la cola de procesamiento</div>
        </div>
        """, unsafe_allow_html=True)
        
        for video in unregistered:
            col1, col2 = st.columns([4, 1])
            with col1:
                size_mb = int(video.get('size', 0)) / (1024 * 1024)
                st.markdown(f"""
                <div style="background-color: white; padding: 12px 15px; border-radius: 8px; border: 1px solid #eee; margin: 5px 0;">
                    <span style="font-size: 1.2rem; margin-right: 10px;">📹</span>
                    <strong>{video['name']}</strong>
                    <span style="color: #666; margin-left: 10px;">({size_mb:.1f} MB)</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("➕ Añadir", key=f"add_{video['id']}"):
                    row_data = [video['name'], "", "", "Pendiente de rellenar", ""]
                    if add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_data):
                        st.toast(f"✅ '{video['name']}' añadido", icon="✅")
                        st.rerun()
        
        st.markdown("")
        if st.button("➕ Añadir todos al Sheet", type="primary", use_container_width=True):
            for video in unregistered:
                add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], 
                               [video['name'], "", "", "Pendiente de rellenar", ""])
            st.toast(f"✅ {len(unregistered)} vídeos añadidos", icon="✅")
            time.sleep(0.5)
            st.rerun()
    else:
        st.markdown("""
        <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 10px;">✅</div>
            <div style="font-size: 1.1rem; color: #2e7d32;">Todo sincronizado correctamente</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Estado del sistema
    st.markdown("#### 📊 Estado del sistema")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        - **Vídeos en Drive:** {len(videos_in_drive)}
        - **Registros en Sheet:** {len(df)}
        """)
    with col2:
        st.markdown(f"""
        - **Pendientes de título:** {len(df[df['Título'].str.strip() == ''])}
        - **Subidos a YouTube:** {len(df[df['Estado'].str.contains('Subido', case=False, na=False)])}
        """)


def render_setup_instructions():
    """Instrucciones de configuración"""
    st.markdown('<p class="main-header">🎬 YouTube Shorts Automation</p>', unsafe_allow_html=True)
    
    st.error("⚠️ Configuración no encontrada")
    
    st.markdown("""
    ### Configuración inicial
    
    Configura los **Secrets** en Streamlit Cloud:
    
    1. Ve a tu app en [share.streamlit.io](https://share.streamlit.io)
    2. Clic en **Settings** → **Secrets**
    3. Pega la configuración con tus valores
    4. Clic en **Save**
    """)


def main():
    """Función principal"""
    config = get_config()
    credentials = get_credentials()
    
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
    
    st.markdown("<br>", unsafe_allow_html=True)
    
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
    st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.85rem;">
        📧 Notificaciones a: {config['notification_email']} | ⏱️ Procesamiento automático cada 5 min
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
