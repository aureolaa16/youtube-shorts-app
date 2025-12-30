"""
YouTube Shorts Automation - Web App v6
- Flujo de trabajo visual
- Tiempos estimados
- Mejor UX en rellenar datos
- Estados claros
"""

import streamlit as st
import pandas as pd
import json
import os
import tempfile
import time
from datetime import datetime, timedelta
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

# ============== CONFIGURACIÓN ==============

def get_config():
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
    /* Header */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1a73e8;
        margin-bottom: 5px;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 25px;
    }
    
    /* Workflow Steps */
    .workflow-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
    }
    .workflow-step {
        text-align: center;
        flex: 1;
        padding: 15px;
        position: relative;
    }
    .workflow-step-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px;
        font-size: 1.5rem;
        transition: all 0.3s;
    }
    .workflow-step-active .workflow-step-icon {
        background: linear-gradient(135deg, #1a73e8, #0d47a1);
        color: white;
        box-shadow: 0 4px 15px rgba(26, 115, 232, 0.4);
    }
    .workflow-step-completed .workflow-step-icon {
        background: linear-gradient(135deg, #4caf50, #2e7d32);
        color: white;
    }
    .workflow-step-pending .workflow-step-icon {
        background: #e0e0e0;
        color: #999;
    }
    .workflow-step-title {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }
    .workflow-step-desc {
        font-size: 0.75rem;
        color: #666;
    }
    .workflow-arrow {
        color: #ccc;
        font-size: 1.5rem;
        padding: 0 10px;
    }
    
    /* Cards */
    .info-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 15px;
        border-left: 4px solid #1a73e8;
    }
    .success-card {
        border-left-color: #4caf50;
        background: #f8fdf8;
    }
    .warning-card {
        border-left-color: #ff9800;
        background: #fffdf5;
    }
    .error-card {
        border-left-color: #f44336;
        background: #fef8f8;
    }
    
    /* Video Card */
    .video-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        transition: all 0.3s;
        border: 1px solid #eee;
    }
    .video-card:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }
    .video-card-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 15px;
        border-bottom: 1px solid #f0f0f0;
    }
    .video-icon {
        font-size: 2.5rem;
        margin-right: 15px;
    }
    .video-info h3 {
        margin: 0 0 5px 0;
        font-size: 1.1rem;
        color: #333;
    }
    .video-meta {
        font-size: 0.85rem;
        color: #888;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .status-pending {
        background: #fff3e0;
        color: #e65100;
    }
    .status-ready {
        background: #e3f2fd;
        color: #1565c0;
    }
    .status-processing {
        background: #f3e5f5;
        color: #7b1fa2;
        animation: pulse 1.5s infinite;
    }
    .status-completed {
        background: #e8f5e9;
        color: #2e7d32;
    }
    .status-error {
        background: #ffebee;
        color: #c62828;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* Time Indicator */
    .time-indicator {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        padding: 15px 20px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        gap: 15px;
        margin: 15px 0;
    }
    .time-icon {
        font-size: 2rem;
    }
    .time-info h4 {
        margin: 0;
        font-size: 0.9rem;
        color: #1565c0;
    }
    .time-info p {
        margin: 5px 0 0 0;
        font-size: 0.8rem;
        color: #666;
    }
    
    /* Character Counter */
    .char-counter {
        font-size: 0.75rem;
        text-align: right;
        margin-top: 5px;
    }
    .char-ok { color: #4caf50; }
    .char-warning { color: #ff9800; }
    .char-error { color: #f44336; }
    
    /* Tips Box */
    .tips-box {
        background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
        padding: 15px 20px;
        border-radius: 10px;
        margin: 15px 0;
    }
    .tips-box h4 {
        margin: 0 0 10px 0;
        color: #2e7d32;
        font-size: 0.9rem;
    }
    .tips-box ul {
        margin: 0;
        padding-left: 20px;
        color: #555;
        font-size: 0.85rem;
    }
    
    /* Metrics */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #666;
    }
    
    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 50px 20px;
        background: #fafafa;
        border-radius: 12px;
        border: 2px dashed #e0e0e0;
    }
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 15px;
    }
    .empty-state h3 {
        margin: 0 0 10px 0;
        color: #666;
    }
    .empty-state p {
        color: #999;
        font-size: 0.9rem;
    }
    
    /* Progress Upload */
    .upload-progress {
        background: #f5f5f5;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
    }
    .upload-file-item {
        background: white;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #1a73e8;
    }
    .upload-file-item.completed {
        border-left-color: #4caf50;
    }
    .upload-file-item.error {
        border-left-color: #f44336;
    }
    
    /* Hashtag Suggestions */
    .hashtag-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }
    .hashtag {
        background: #e3f2fd;
        color: #1565c0;
        padding: 5px 12px;
        border-radius: 15px;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .hashtag:hover {
        background: #1565c0;
        color: white;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        background: #f5f5f5;
        padding: 5px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


# ============== SERVICIOS ==============

def get_drive_service(credentials):
    return build('drive', 'v3', credentials=credentials)

def get_sheets_service(credentials):
    return build('sheets', 'v4', credentials=credentials)

def list_videos_in_folder(drive_service, folder_id):
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
        st.error(f"Error: {e}")
        return pd.DataFrame(columns=['Nombre archivo', 'Título', 'Descripción', 'Estado', 'YouTube URL'])

def add_row_to_sheet(sheets_service, spreadsheet_id, sheet_name, row_data):
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
    except:
        return False

def update_sheet_row(sheets_service, spreadsheet_id, sheet_name, row_num, titulo, descripcion):
    try:
        range_name = f"'{sheet_name}'!B{row_num}:C{row_num}"
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body={"values": [[titulo, descripcion]]}
        ).execute()
        return True
    except:
        return False

def upload_video_to_drive(drive_service, folder_id, file, filename, progress_callback=None):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(file.getbuffer())
            tmp_path = tmp.name
        
        file_metadata = {'name': filename, 'parents': [folder_id]}
        file_size = os.path.getsize(tmp_path)
        
        media = MediaFileUpload(tmp_path, resumable=True, chunksize=1024*1024)
        request = drive_service.files().create(body=file_metadata, media_body=media, fields='id, name')
        
        response = None
        start_time = time.time()
        
        while response is None:
            status, response = request.next_chunk()
            if status and progress_callback:
                elapsed = time.time() - start_time
                speed = (status.progress() * file_size) / elapsed if elapsed > 0 else 0
                remaining = ((1 - status.progress()) * elapsed / status.progress()) if status.progress() > 0 else 0
                progress_callback(status.progress(), speed, remaining)
        
        os.unlink(tmp_path)
        return response
    except Exception as e:
        st.error(f"Error: {e}")
        return None


# ============== HELPERS ==============

def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024*1024:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/(1024*1024):.1f} MB"

def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.0f} seg"
    else:
        return f"{seconds/60:.1f} min"

def estimate_upload_time(size_bytes):
    # Estimación basada en 1 MB/s promedio
    seconds = size_bytes / (1024 * 1024)
    return max(5, seconds)  # Mínimo 5 segundos

def get_next_process_time():
    """Calcula cuándo será el próximo procesamiento (cada 5 min)"""
    now = datetime.now()
    minutes = now.minute
    next_5 = ((minutes // 5) + 1) * 5
    if next_5 >= 60:
        next_time = now.replace(minute=0, second=0) + timedelta(hours=1)
    else:
        next_time = now.replace(minute=next_5, second=0)
    diff = (next_time - now).seconds
    return diff

def get_video_status_info(estado, titulo):
    """Devuelve información del estado del vídeo"""
    if 'Subido' in estado:
        return ('completed', '✅ Publicado', 'Tu Short ya está en YouTube')
    elif 'Error' in estado:
        return ('error', '❌ Error', estado)
    elif titulo.strip():
        return ('ready', '🚀 Listo', 'Se subirá en el próximo ciclo')
    else:
        return ('pending', '✏️ Pendiente', 'Añade título para procesar')


# ============== COMPONENTES UI ==============

def render_workflow_status(df, videos_in_drive):
    """Muestra el flujo de trabajo visual"""
    pending = len(df[(df['Título'].str.strip() == '') | (df['Estado'].str.contains('Pendiente', case=False, na=True))])
    ready = len(df[(df['Título'].str.strip() != '') & (~df['Estado'].str.contains('Subido', case=False, na=False)) & (~df['Estado'].str.contains('Error', case=False, na=False)) & (~df['Estado'].str.contains('Pendiente', case=False, na=True))])
    uploaded = len(df[df['Estado'].str.contains('Subido', case=False, na=False)])
    
    # Determinar paso activo
    if len(videos_in_drive) == 0 and len(df) == 0:
        active_step = 1
    elif pending > 0:
        active_step = 2
    elif ready > 0:
        active_step = 3
    else:
        active_step = 4
    
    st.markdown(f"""
    <div class="workflow-container">
        <div class="workflow-step {'workflow-step-completed' if len(df) > 0 else 'workflow-step-active' if active_step == 1 else 'workflow-step-pending'}">
            <div class="workflow-step-icon">📤</div>
            <div class="workflow-step-title">1. Subir vídeo</div>
            <div class="workflow-step-desc">{len(videos_in_drive)} en Drive</div>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step {'workflow-step-completed' if pending == 0 and len(df) > 0 else 'workflow-step-active' if active_step == 2 else 'workflow-step-pending'}">
            <div class="workflow-step-icon">✏️</div>
            <div class="workflow-step-title">2. Rellenar datos</div>
            <div class="workflow-step-desc">{pending} pendientes</div>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step {'workflow-step-active' if active_step == 3 else 'workflow-step-pending'}">
            <div class="workflow-step-icon">⚙️</div>
            <div class="workflow-step-title">3. Procesando</div>
            <div class="workflow-step-desc">{ready} en cola</div>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step {'workflow-step-completed' if uploaded > 0 else 'workflow-step-pending'}">
            <div class="workflow-step-icon">🎬</div>
            <div class="workflow-step-title">4. En YouTube</div>
            <div class="workflow-step-desc">{uploaded} publicados</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_time_indicator():
    """Muestra el tiempo hasta el próximo procesamiento"""
    next_process = get_next_process_time()
    minutes = next_process // 60
    seconds = next_process % 60
    
    st.markdown(f"""
    <div class="time-indicator">
        <div class="time-icon">⏱️</div>
        <div class="time-info">
            <h4>Próximo procesamiento automático</h4>
            <p>En aproximadamente <strong>{minutes}:{seconds:02d}</strong> minutos</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_upload_tab(drive_service, sheets_service, config):
    """Tab de subida mejorado"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📤 Subir vídeos")
        st.markdown("Arrastra tus vídeos aquí. Se guardarán en Drive y podrás añadir título después.")
    
    with col2:
        st.markdown("""
        <div class="tips-box">
            <h4>💡 Requisitos para Shorts</h4>
            <ul>
                <li>Formato vertical (9:16)</li>
                <li>Máximo 60 segundos</li>
                <li>MP4, MOV o AVI</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Arrastra o selecciona vídeos",
        type=['mp4', 'mov', 'avi'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        total_size = sum(f.size for f in uploaded_files)
        total_time = sum(estimate_upload_time(f.size) for f in uploaded_files)
        
        st.markdown(f"""
        <div class="info-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{len(uploaded_files)} vídeo(s) seleccionado(s)</strong>
                    <span style="color: #666; margin-left: 15px;">{format_size(total_size)} total</span>
                </div>
                <div style="color: #1a73e8;">
                    ⏱️ Tiempo estimado: ~{format_time(total_time)}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for file in uploaded_files:
            est_time = estimate_upload_time(file.size)
            st.markdown(f"""
            <div class="upload-file-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 1.3rem; margin-right: 10px;">📹</span>
                        <strong>{file.name}</strong>
                    </div>
                    <div style="color: #666; font-size: 0.85rem;">
                        {format_size(file.size)} · ~{format_time(est_time)}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🚀 Subir todos a Drive", type="primary", use_container_width=True):
            progress_container = st.container()
            
            with progress_container:
                overall_progress = st.progress(0)
                results = []
                
                for i, file in enumerate(uploaded_files):
                    status_placeholder = st.empty()
                    progress_placeholder = st.progress(0)
                    detail_placeholder = st.empty()
                    
                    status_placeholder.markdown(f"""
                    <div class="upload-file-item">
                        <div style="display: flex; align-items: center;">
                            <span class="status-badge status-processing">⏳ Subiendo...</span>
                            <strong style="margin-left: 15px;">{file.name}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    def update_progress(progress, speed, remaining):
                        progress_placeholder.progress(progress)
                        detail_placeholder.markdown(f"""
                        <div style="display: flex; justify-content: space-between; color: #666; font-size: 0.8rem; padding: 5px 10px;">
                            <span>⚡ {format_size(speed)}/s</span>
                            <span>⏱️ {format_time(remaining)} restante</span>
                            <span>📊 {progress*100:.0f}%</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    result = upload_video_to_drive(
                        drive_service, config['folder_videos'],
                        file, file.name, update_progress
                    )
                    
                    if result:
                        add_row_to_sheet(sheets_service, config['spreadsheet_id'], 
                                        config['sheet_name'], [file.name, "", "", "Pendiente de rellenar", ""])
                        status_placeholder.markdown(f"""
                        <div class="upload-file-item completed">
                            <div style="display: flex; align-items: center;">
                                <span class="status-badge status-completed">✅ Completado</span>
                                <strong style="margin-left: 15px;">{file.name}</strong>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        results.append(True)
                    else:
                        status_placeholder.markdown(f"""
                        <div class="upload-file-item error">
                            <div style="display: flex; align-items: center;">
                                <span class="status-badge status-error">❌ Error</span>
                                <strong style="margin-left: 15px;">{file.name}</strong>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        results.append(False)
                    
                    progress_placeholder.empty()
                    detail_placeholder.empty()
                    overall_progress.progress((i + 1) / len(uploaded_files))
                
                success_count = sum(results)
                if success_count == len(uploaded_files):
                    st.success(f"🎉 ¡{success_count} vídeo(s) subido(s) correctamente!")
                    st.balloons()
                    st.info("👉 Ahora ve a **'✏️ Rellenar datos'** para añadir títulos y descripciones")
                else:
                    st.warning(f"⚠️ {success_count}/{len(uploaded_files)} subidos correctamente")


def render_edit_tab(sheets_service, config, df):
    """Tab de edición mejorado"""
    
    st.markdown("### ✏️ Rellenar títulos y descripciones")
    
    # Time indicator
    render_time_indicator()
    
    # Filtrar pendientes
    pending_df = df[
        (df['Título'].str.strip() == '') | 
        (df['Estado'].str.contains('Pendiente', case=False, na=True)) |
        (df['Estado'] == '')
    ].copy()
    
    if pending_df.empty:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🎉</div>
            <h3>¡Todo listo!</h3>
            <p>No hay vídeos pendientes de rellenar. Sube nuevos vídeos en la pestaña anterior.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"""
    <div class="info-card warning-card">
        <strong>📝 {len(pending_df)} vídeo(s) esperando título</strong>
        <p style="margin: 5px 0 0 0; font-size: 0.85rem; color: #666;">
            Añade título y descripción para que se procesen automáticamente
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sugerencias de hashtags
    hashtags = ["#Shorts", "#Viral", "#Trending", "#FYP", "#Funny", "#Tutorial", "#Tips"]
    
    for idx, row in pending_df.iterrows():
        status_class, status_text, status_desc = get_video_status_info(row['Estado'], row['Título'])
        
        with st.container():
            st.markdown(f"""
            <div class="video-card">
                <div class="video-card-header">
                    <div class="video-icon">📹</div>
                    <div class="video-info">
                        <h3>{row['Nombre archivo']}</h3>
                        <div class="video-meta">
                            <span class="status-badge status-{status_class}">{status_text}</span>
                            <span style="margin-left: 10px; color: #888;">{status_desc}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_titulo = st.text_input(
                    "Título del Short",
                    value=row['Título'],
                    key=f"titulo_{idx}",
                    max_chars=100,
                    placeholder="Escribe un título atractivo..."
                )
                
                # Contador de caracteres
                char_count = len(new_titulo)
                char_class = "char-ok" if char_count <= 70 else ("char-warning" if char_count <= 90 else "char-error")
                st.markdown(f"""
                <div class="char-counter {char_class}">
                    {char_count}/100 caracteres {'✓' if char_count <= 70 else '⚠️' if char_count <= 90 else '⛔'}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                new_descripcion = st.text_area(
                    "Descripción",
                    value=row['Descripción'],
                    key=f"desc_{idx}",
                    height=100,
                    placeholder="Añade una descripción con hashtags..."
                )
            
            # Hashtags sugeridos
            st.markdown("**Hashtags sugeridos:** (clic para copiar)")
            hashtag_cols = st.columns(len(hashtags))
            for i, tag in enumerate(hashtags):
                with hashtag_cols[i]:
                    if st.button(tag, key=f"hash_{idx}_{i}", use_container_width=True):
                        st.toast(f"Añade {tag} a tu descripción", icon="📋")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            
            with col_btn1:
                if st.button("💾 Guardar", key=f"save_{idx}", type="primary", use_container_width=True):
                    if new_titulo.strip():
                        row_num = idx + 2
                        if update_sheet_row(sheets_service, config['spreadsheet_id'], config['sheet_name'], row_num, new_titulo, new_descripcion):
                            st.toast("✅ Guardado correctamente", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.toast("⚠️ El título es obligatorio", icon="⚠️")
            
            with col_btn2:
                if new_titulo.strip():
                    st.markdown(f"""
                    <div style="padding: 8px; text-align: center; color: #4caf50; font-size: 0.85rem;">
                        ✅ Listo para procesar
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")


def render_history_tab(df):
    """Tab de historial mejorado"""
    
    st.markdown("### 📊 Shorts publicados en YouTube")
    
    uploaded_df = df[df['Estado'].str.contains('Subido', case=False, na=False)].copy()
    
    if uploaded_df.empty:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <h3>Aún no hay vídeos publicados</h3>
            <p>Los vídeos aparecerán aquí cuando se suban a YouTube</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"""
    <div class="info-card success-card">
        <strong>🎬 {len(uploaded_df)} Short(s) publicado(s)</strong>
    </div>
    """, unsafe_allow_html=True)
    
    for idx, row in uploaded_df.iterrows():
        st.markdown(f"""
        <div class="video-card" style="border-left: 4px solid #4caf50;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h3 style="margin: 0 0 8px 0; color: #333;">{row['Título']}</h3>
                    <p style="margin: 0 0 5px 0; color: #666; font-size: 0.85rem;">📁 {row['Nombre archivo']}</p>
                    <p style="margin: 0; color: #888; font-size: 0.85rem;">{row['Descripción'][:100]}{'...' if len(row['Descripción']) > 100 else ''}</p>
                </div>
                <span class="status-badge status-completed">✅ Publicado</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if row['YouTube URL']:
            st.link_button("▶️ Ver en YouTube", row['YouTube URL'], use_container_width=False)
        st.markdown("")


def render_sync_tab(drive_service, sheets_service, config, df, videos_in_drive):
    """Tab de sincronización"""
    
    st.markdown("### 🔄 Sincronización")
    
    sheet_filenames = set(df['Nombre archivo'].str.lower())
    unregistered = [v for v in videos_in_drive if v['name'].lower() not in sheet_filenames]
    
    if unregistered:
        st.markdown(f"""
        <div class="info-card warning-card">
            <strong>⚠️ {len(unregistered)} vídeo(s) en Drive sin registrar</strong>
            <p style="margin: 5px 0 0 0; font-size: 0.85rem;">Estos vídeos están en Drive pero no en la cola de procesamiento</p>
        </div>
        """, unsafe_allow_html=True)
        
        for video in unregistered:
            col1, col2 = st.columns([4, 1])
            with col1:
                size_mb = int(video.get('size', 0)) / (1024 * 1024)
                st.markdown(f"📹 **{video['name']}** ({size_mb:.1f} MB)")
            with col2:
                if st.button("➕ Añadir", key=f"add_{video['id']}"):
                    add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'],
                                    [video['name'], "", "", "Pendiente de rellenar", ""])
                    st.toast("✅ Añadido", icon="✅")
                    st.rerun()
        
        if st.button("➕ Añadir todos", type="primary"):
            for video in unregistered:
                add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'],
                                [video['name'], "", "", "Pendiente de rellenar", ""])
            st.toast(f"✅ {len(unregistered)} añadidos", icon="✅")
            st.rerun()
    else:
        st.markdown("""
        <div class="info-card success-card">
            <strong>✅ Todo sincronizado</strong>
            <p style="margin: 5px 0 0 0; font-size: 0.85rem;">Todos los vídeos de Drive están registrados</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Estadísticas
    st.markdown("#### 📊 Estado del sistema")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #1a73e8;">{len(videos_in_drive)}</div>
            <div class="metric-label">En Drive</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pending = len(df[df['Título'].str.strip() == ''])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #ff9800;">{pending}</div>
            <div class="metric-label">Sin título</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        ready = len(df[(df['Título'].str.strip() != '') & (~df['Estado'].str.contains('Subido', case=False, na=False))])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #2196f3;">{ready}</div>
            <div class="metric-label">En cola</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        uploaded = len(df[df['Estado'].str.contains('Subido', case=False, na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #4caf50;">{uploaded}</div>
            <div class="metric-label">Publicados</div>
        </div>
        """, unsafe_allow_html=True)


def render_help_section():
    """Sección de ayuda colapsable"""
    with st.expander("❓ ¿Cómo funciona?"):
        st.markdown("""
        ### Flujo de trabajo
        
        1. **📤 Subir vídeos**: Arrastra tus vídeos o súbelos directamente a la carpeta de Drive
        2. **✏️ Rellenar datos**: Añade título y descripción cuando quieras
        3. **⚙️ Procesamiento**: Cada 5 minutos, el sistema sube automáticamente los vídeos con título
        4. **🎬 Publicado**: Recibes un email y el vídeo aparece en el historial
        
        ### Preguntas frecuentes
        
        **¿Cuánto tarda en subirse a YouTube?**
        - Máximo 5 minutos después de añadir el título
        
        **¿Puedo subir vídeos directamente a Drive?**
        - Sí, luego ve a "Sincronizar" para añadirlos a la cola
        
        **¿Por qué mi vídeo está en errores?**
        - Puede ser límite diario de YouTube o formato incorrecto
        """)


def main():
    config = get_config()
    credentials = get_credentials()
    
    if not config or not credentials:
        st.error("⚠️ Configuración no encontrada. Configura los Secrets en Streamlit Cloud.")
        return
    
    # Header
    st.markdown('<p class="main-header">🎬 YouTube Shorts Automation</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Automatiza la publicación de tus Shorts de forma sencilla</p>', unsafe_allow_html=True)
    
    # Servicios
    drive_service = get_drive_service(credentials)
    sheets_service = get_sheets_service(credentials)
    
    # Datos
    df = get_sheet_data(sheets_service, config['spreadsheet_id'], config['sheet_name'])
    videos_in_drive = list_videos_in_folder(drive_service, config['folder_videos'])
    
    # Workflow visual
    render_workflow_status(df, videos_in_drive)
    
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
    
    # Help section
    render_help_section()
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #888; font-size: 0.8rem;">
        📧 Notificaciones: {config['notification_email']} | ⏱️ Procesamiento cada 5 min | 🔄 Actualiza para ver cambios
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
