"""
YouTube Shorts Automation - Web App v11
"""

import streamlit as st
import pandas as pd
import os
import tempfile
import time
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

st.set_page_config(
    page_title="YouTube Shorts Automation",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============== ESTILOS ==============
st.markdown("""
<style>
    .main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 15px 0;
        border-bottom: 3px solid #ff0000;
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 15px;
    }
    .main-header-left {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .main-header-left img {
        height: 45px;
    }
    .main-header-left h1 {
        color: #ff0000;
        font-size: 2rem;
        margin: 0;
        font-weight: bold;
    }
    .main-header-right {
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
    }
    .stat-pill {
        background: #f0f0f0;
        padding: 8px 15px;
        border-radius: 20px;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .stat-pill.pending { background: #fff3e0; color: #e65100; }
    .stat-pill.queue { background: #e3f2fd; color: #1565c0; }
    .stat-pill.done { background: #e8f5e9; color: #2e7d32; }
    .stat-pill.error { background: #ffebee; color: #c62828; }
    
    .queue-card {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-left: 5px solid #4caf50;
        padding: 15px 20px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    .queue-card-title {
        font-weight: bold;
        font-size: 1.1rem;
        color: #2e7d32;
    }
    .queue-card-file {
        color: #666;
        font-size: 0.9rem;
    }
    .queue-card-time {
        background: #4caf50;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .pending-card {
        background: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .stats-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
    }
    .stats-number {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .stats-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Notificación global */
    .global-notification {
        background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 15px;
        animation: slideIn 0.5s ease-out;
    }
    .global-notification.error {
        background: linear-gradient(135deg, #f44336 0%, #c62828 100%);
    }
    @keyframes slideIn {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    .global-notification-icon {
        font-size: 2rem;
    }
    .global-notification-text {
        flex: 1;
    }
    .global-notification-title {
        font-weight: bold;
        font-size: 1.1rem;
    }
    .global-notification-subtitle {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Preview mejorado */
    .video-preview {
        background: #0f0f0f;
        border-radius: 12px;
        overflow: hidden;
        max-width: 280px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .video-preview-player {
        background: linear-gradient(180deg, #1a1a1a 0%, #0a0a0a 100%);
        height: 380px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;
    }
    .video-preview-player::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%23222" width="100" height="100"/><circle cx="50" cy="50" r="20" fill="%23333"/><polygon points="45,40 45,60 62,50" fill="%23555"/></svg>');
        background-size: cover;
        opacity: 0.5;
    }
    .video-preview-play {
        width: 60px;
        height: 60px;
        background: rgba(255,255,255,0.9);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1;
    }
    .video-preview-play::after {
        content: '';
        border-style: solid;
        border-width: 12px 0 12px 20px;
        border-color: transparent transparent transparent #ff0000;
        margin-left: 4px;
    }
    .video-preview-info {
        padding: 12px 15px;
        background: #0f0f0f;
    }
    .video-preview-title {
        color: #fff;
        font-weight: 500;
        font-size: 0.95rem;
        margin-bottom: 8px;
        line-height: 1.3;
    }
    .video-preview-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #aaa;
        font-size: 0.8rem;
    }
    .video-preview-channel {
        width: 24px;
        height: 24px;
        background: #ff0000;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 0.7rem;
        font-weight: bold;
    }
    .video-preview-desc {
        color: #888;
        font-size: 0.8rem;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

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

# ============== SERVICIOS ==============

def get_drive_service(credentials):
    return build('drive', 'v3', credentials=credentials)

def get_sheets_service(credentials):
    return build('sheets', 'v4', credentials=credentials)

def list_videos_in_folder(drive_service, folder_id):
    try:
        query = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id, name, createdTime, size)", orderBy="createdTime desc").execute()
        return results.get('files', [])
    except:
        return []

def get_sheet_data(sheets_service, spreadsheet_id, sheet_name):
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A:G"
        ).execute()
        rows = result.get('values', [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=['Nombre archivo', 'Título', 'Descripción', 'Estado', 'YouTube URL', 'Fecha subida', 'Fecha publicación'])
        headers = ['Nombre archivo', 'Título', 'Descripción', 'Estado', 'YouTube URL', 'Fecha subida', 'Fecha publicación']
        data = []
        for row in rows[1:]:
            while len(row) < 7:
                row.append('')
            data.append(row[:7])
        return pd.DataFrame(data, columns=headers)
    except:
        return pd.DataFrame(columns=['Nombre archivo', 'Título', 'Descripción', 'Estado', 'YouTube URL', 'Fecha subida', 'Fecha publicación'])

def add_row_to_sheet(sheets_service, spreadsheet_id, sheet_name, row_data):
    try:
        if len(row_data) < 6:
            row_data.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        if len(row_data) < 7:
            row_data.append('')
        sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A:G",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row_data]}
        ).execute()
        return True
    except:
        return False

def update_sheet_row(sheets_service, spreadsheet_id, sheet_name, row_num, titulo, descripcion):
    try:
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!B{row_num}:C{row_num}",
            valueInputOption="RAW",
            body={"values": [[titulo, descripcion]]}
        ).execute()
        return True
    except:
        return False

def upload_video_to_drive(drive_service, folder_id, file, filename, progress_cb=None):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(file.getbuffer())
            tmp_path = tmp.name
        media = MediaFileUpload(tmp_path, resumable=True, chunksize=1024*1024)
        request = drive_service.files().create(
            body={'name': filename, 'parents': [folder_id]},
            media_body=media,
            fields='id, name'
        )
        response = None
        start = time.time()
        file_size = os.path.getsize(tmp_path)
        while response is None:
            status, response = request.next_chunk()
            if status and progress_cb:
                elapsed = time.time() - start
                speed = (status.progress() * file_size) / elapsed if elapsed > 0 else 0
                progress_cb(status.progress(), speed)
        os.unlink(tmp_path)
        return response
    except:
        return None

# ============== HELPERS ==============

def format_size(b):
    if b < 1024: return f"{b} B"
    if b < 1024**2: return f"{b/1024:.1f} KB"
    return f"{b/1024**2:.1f} MB"

def get_next_process_time():
    now = datetime.now()
    minutes = now.minute
    next_5 = ((minutes // 5) + 1) * 5
    if next_5 >= 60:
        target = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        target = now.replace(minute=next_5, second=0, microsecond=0)
    diff = target - now
    return int(diff.total_seconds())

def format_countdown(seconds):
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"

def get_counts(df):
    pendientes = len(df[(df['Título'].str.strip() == '') & (~df['Estado'].str.contains('Subido|Error|Borrado', case=False, na=False, regex=True))])
    en_cola = len(df[(df['Título'].str.strip() != '') & (~df['Estado'].str.contains('Subido|Error|Borrado', case=False, na=False, regex=True))])
    subidos = len(df[df['Estado'].str.contains('Subido', case=False, na=False)])
    errores = len(df[df['Estado'].str.contains('Error', case=False, na=False)])
    return pendientes, en_cola, subidos, errores

# ============== PÁGINAS ==============

def render_upload_tab(drive_service, sheets_service, config):
    st.markdown("### 📤 Subir vídeos a Drive")
    
    # Si acaba de subir, mostrar solo mensaje de éxito
    if st.session_state.get('just_uploaded', False):
        st.success("🎉 **¡Vídeos subidos correctamente!**")
        st.info("👉 Ve a la pestaña **'✏️ Rellenar'** para añadir títulos a tus vídeos.")
        
        if st.button("📤 Subir más vídeos", type="primary"):
            st.session_state.just_uploaded = False
            st.rerun()
        return
    
    st.info("💡 **Paso 1:** Sube tus vídeos aquí. Se guardarán en Google Drive automáticamente.")
    
    files = st.file_uploader("Arrastra tus vídeos aquí", type=['mp4', 'mov', 'avi'], accept_multiple_files=True)
    
    if files:
        total_size = sum(f.size for f in files)
        st.write(f"📁 **{len(files)} vídeo(s)** seleccionado(s) - {format_size(total_size)} total")
        
        if st.button("🚀 Subir a Drive", type="primary", use_container_width=True):
            progress = st.progress(0)
            status_text = st.empty()
            
            uploaded_count = 0
            for i, f in enumerate(files):
                status_text.write(f"⏳ Subiendo **{f.name}**...")
                file_progress = st.progress(0)
                
                def update(p, speed):
                    file_progress.progress(p)
                
                result = upload_video_to_drive(drive_service, config['folder_videos'], f, f.name, update)
                
                if result:
                    add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], 
                                    [f.name, "", "", "Pendiente de rellenar", ""])
                    uploaded_count += 1
                
                file_progress.empty()
                progress.progress((i + 1) / len(files))
            
            status_text.empty()
            progress.empty()
            
            if uploaded_count > 0:
                st.balloons()
                st.session_state.just_uploaded = True
                st.rerun()


def render_edit_tab(sheets_service, config, df):
    # Header con refresh
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### ✏️ Rellenar títulos y descripciones")
    with col_refresh:
        if st.button("🔄 Actualizar", key="refresh_edit", use_container_width=True):
            st.rerun()
    
    # Mostrar mensaje si acaba de guardar - SE QUEDA EN ESTA PESTAÑA
    if st.session_state.get('just_saved_to_queue', False):
        saved_count = st.session_state.get('saved_count', 0)
        st.markdown(f"""
        <div class="global-notification">
            <div class="global-notification-icon">✅</div>
            <div class="global-notification-text">
                <div class="global-notification-title">¡{saved_count} vídeo(s) guardado(s) correctamente!</div>
                <div class="global-notification-subtitle">Ya están en la cola y se subirán a YouTube en el próximo procesamiento</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.just_saved_to_queue = False
    
    # Solo vídeos SIN título (no subidos, no error, no borrado)
    sin_titulo = df[
        (df['Título'].str.strip() == '') & 
        (~df['Estado'].str.contains('Subido|Error|Borrado', case=False, na=False, regex=True))
    ].copy()
    
    if sin_titulo.empty:
        st.success("🎉 ¡Todo listo! No hay vídeos pendientes de rellenar.")
        st.info("👉 Sube más vídeos en la pestaña **'📤 Subir'** o revisa los que están **'🚀 En cola'**")
        return
    
    st.warning(f"📝 **{len(sin_titulo)} vídeo(s)** esperando título. Rellena los datos para que se procesen.")
    
    # Botones de acción
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        save_all = st.button("💾 Guardar todos", type="primary", use_container_width=True)
    with col3:
        delete_mode = st.checkbox("🗑️ Modo borrar", help="Activa para poder borrar vídeos")
    
    st.divider()
    
    # Formularios
    videos_data = {}
    
    for idx, row in sin_titulo.iterrows():
        st.markdown(f"""
        <div class="pending-card">
            <strong>📹 {row['Nombre archivo']}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        if delete_mode:
            col_title_input, col_desc, col_delete = st.columns([3, 2.5, 1])
        else:
            col_title_input, col_desc, col_preview, col_btn = st.columns([3, 2.5, 0.5, 1])
        
        with col_title_input:
            titulo = st.text_input("Título *", key=f"t_{idx}", placeholder="Escribe el título del Short...", label_visibility="collapsed")
        
        with col_desc:
            desc = st.text_input("Descripción", key=f"d_{idx}", placeholder="Descripción (opcional)", label_visibility="collapsed")
        
        if delete_mode:
            with col_delete:
                if st.button("🗑️", key=f"del_{idx}", help="Borrar este vídeo", use_container_width=True):
                    try:
                        sheets_service.spreadsheets().values().update(
                            spreadsheetId=config['spreadsheet_id'],
                            range=f"'{config['sheet_name']}'!D{idx + 2}",
                            valueInputOption="RAW",
                            body={"values": [["Borrado"]]}
                        ).execute()
                        st.toast("🗑️ Vídeo borrado")
                        time.sleep(0.3)
                        st.rerun()
                    except:
                        st.toast("❌ Error al borrar")
        else:
            with col_preview:
                preview = st.checkbox("👁️", key=f"p_{idx}", help="Previsualizar")
            
            with col_btn:
                if st.button("💾", key=f"s_{idx}", help="Guardar este vídeo", use_container_width=True):
                    if titulo.strip():
                        if update_sheet_row(sheets_service, config['spreadsheet_id'], config['sheet_name'], idx + 2, titulo, desc):
                            st.session_state.just_saved_to_queue = True
                            st.session_state.saved_count = 1
                            st.rerun()
                        else:
                            st.toast("❌ Error al guardar")
                    else:
                        st.toast("⚠️ El título es obligatorio")
            
            # Previsualización MEJORADA estilo YouTube
            if preview:
                display_title = titulo if titulo else "Sin título..."
                display_desc = desc[:80] + '...' if desc and len(desc) > 80 else desc if desc else "Sin descripción"
                
                st.markdown(f"""
                <div class="video-preview">
                    <div class="video-preview-player">
                        <div class="video-preview-play"></div>
                    </div>
                    <div class="video-preview-info">
                        <div class="video-preview-title">{display_title}</div>
                        <div class="video-preview-meta">
                            <div class="video-preview-channel">YT</div>
                            <span>Tu Canal · 0 vistas · ahora</span>
                        </div>
                        <div class="video-preview-desc">{display_desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        videos_data[idx] = {'titulo': titulo, 'desc': desc}
        st.write("")
    
    # Guardar todos
    if save_all:
        valid = {k: v for k, v in videos_data.items() if v['titulo'].strip()}
        if not valid:
            st.warning("⚠️ Escribe al menos un título")
        else:
            saved = 0
            for idx, data in valid.items():
                if update_sheet_row(sheets_service, config['spreadsheet_id'], config['sheet_name'], idx + 2, data['titulo'], data['desc']):
                    saved += 1
            st.session_state.just_saved_to_queue = True
            st.session_state.saved_count = saved
            st.rerun()


def render_queue_tab(df):
    # Header con refresh
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### 🚀 Vídeos en cola de procesamiento")
    with col_refresh:
        if st.button("🔄 Actualizar", key="refresh_queue", use_container_width=True):
            st.rerun()
    
    # Mostrar notificación si hay videos recién subidos a YouTube
    if st.session_state.get('new_uploads_to_youtube', 0) > 0:
        count = st.session_state.new_uploads_to_youtube
        st.markdown(f"""
        <div class="global-notification">
            <div class="global-notification-icon">🎉</div>
            <div class="global-notification-text">
                <div class="global-notification-title">¡{count} vídeo(s) subido(s) a YouTube!</div>
                <div class="global-notification-subtitle">Ve al historial para ver los enlaces de tus Shorts</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.new_uploads_to_youtube = 0
    
    # Tiempo hasta próximo procesamiento
    seconds_left = get_next_process_time()
    
    # Vídeos con título pero no subidos ni error ni borrado
    en_cola = df[
        (df['Título'].str.strip() != '') & 
        (~df['Estado'].str.contains('Subido|Error|Borrado', case=False, na=False, regex=True))
    ].copy()
    
    # Mostrar countdown
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stats-box">
            <div class="stats-number">⏱️ {format_countdown(seconds_left)}</div>
            <div class="stats-label">Próximo procesamiento</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stats-box">
            <div class="stats-number">{len(en_cola)}</div>
            <div class="stats-label">Vídeos en cola</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stats-box">
            <div class="stats-number">5 min</div>
            <div class="stats-label">Intervalo de proceso</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    
    if en_cola.empty:
        st.info("📭 No hay vídeos en cola. Ve a **'✏️ Rellenar datos'** para añadir títulos a tus vídeos.")
        return
    
    st.success(f"🎬 **{len(en_cola)} vídeo(s)** listos para subirse a YouTube")
    st.caption("Los vídeos se procesarán automáticamente en el próximo ciclo.")
    
    st.divider()
    
    for idx, row in en_cola.iterrows():
        st.markdown(f"""
        <div class="queue-card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div>
                    <div class="queue-card-title">🎬 {row['Título']}</div>
                    <div class="queue-card-file">📁 {row['Nombre archivo']}</div>
                    {f"<div class='queue-card-file'>📝 {row['Descripción'][:80]}...</div>" if row['Descripción'] and len(row['Descripción']) > 0 else ""}
                </div>
                <div class="queue-card-time">⏳ {format_countdown(seconds_left)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_history_tab(df):
    st.markdown("### 📊 Vídeos publicados en YouTube")
    
    done_df = df[df['Estado'].str.contains('Subido', case=False, na=False)].copy()
    
    if done_df.empty:
        st.info("📭 Aún no hay vídeos publicados. Aparecerán aquí cuando se suban a YouTube.")
        return
    
    st.success(f"🎬 **{len(done_df)} Short(s) publicado(s)** en YouTube")
    
    # Filtro de búsqueda
    col_filter, col_count = st.columns([3, 1])
    with col_filter:
        search = st.text_input("🔍 Buscar por título o archivo", placeholder="Escribe para filtrar...", label_visibility="collapsed")
    with col_count:
        show_count = st.selectbox("Mostrar", [10, 25, 50, 100, "Todos"], index=0, label_visibility="collapsed")
    
    # Aplicar filtro
    if search:
        done_df = done_df[
            done_df['Título'].str.contains(search, case=False, na=False) |
            done_df['Nombre archivo'].str.contains(search, case=False, na=False)
        ]
    
    # Limitar cantidad
    if show_count != "Todos":
        done_df = done_df.head(int(show_count))
    
    st.caption(f"Mostrando {len(done_df)} vídeo(s)")
    st.divider()
    
    for idx, row in done_df.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{row['Título']}**")
            st.caption(f"📁 {row['Nombre archivo']}")
            if row['Descripción']:
                st.caption(f"📝 {row['Descripción'][:100]}")
        with col2:
            if row['YouTube URL']:
                st.link_button("▶️ Ver", row['YouTube URL'], use_container_width=True)
        st.divider()


def render_logs_tab(df):
    st.markdown("### 📋 Logs y Errores")
    
    # Resumen del sistema ARRIBA
    st.markdown("#### 📊 Resumen del sistema")
    
    pendientes, en_cola, subidos, errores = get_counts(df)
    total = len(df)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 Total", total)
    col2.metric("📝 Pendientes", pendientes)
    col3.metric("🚀 En cola", en_cola)
    col4.metric("✅ Subidos", subidos)
    col5.metric("❌ Errores", errores)
    
    st.divider()
    
    # Errores
    st.markdown("#### ❌ Errores")
    
    error_df = df[df['Estado'].str.contains('Error', case=False, na=False)]
    
    if error_df.empty:
        st.success("✅ **Sin errores** - Todos los vídeos se han procesado correctamente")
    else:
        st.error(f"⚠️ **{len(error_df)} vídeo(s) con error**")
        
        # Filtro de errores
        col_filter, col_count = st.columns([3, 1])
        with col_filter:
            error_search = st.text_input("🔍 Buscar error", placeholder="Filtrar por nombre o mensaje...", key="error_search", label_visibility="collapsed")
        with col_count:
            error_count = st.selectbox("Mostrar", [5, 10, 25, "Todos"], index=0, key="error_count", label_visibility="collapsed")
        
        # Aplicar filtros
        filtered_errors = error_df
        if error_search:
            filtered_errors = filtered_errors[
                filtered_errors['Nombre archivo'].str.contains(error_search, case=False, na=False) |
                filtered_errors['Estado'].str.contains(error_search, case=False, na=False)
            ]
        
        if error_count != "Todos":
            filtered_errors = filtered_errors.head(int(error_count))
        
        st.caption(f"Mostrando {len(filtered_errors)} de {len(error_df)} error(es)")
        
        for idx, row in filtered_errors.iterrows():
            with st.expander(f"❌ {row['Nombre archivo']}", expanded=False):
                st.code(row['Estado'])
                
                # Sugerencias según el error
                error_lower = row['Estado'].lower()
                if 'uploadlimitexceeded' in error_lower or 'exceeded' in error_lower:
                    st.info("💡 **Solución:** Has alcanzado el límite diario de YouTube. Espera 24 horas.")
                elif 'quota' in error_lower:
                    st.info("💡 **Solución:** Cuota de API agotada. Se resetea a medianoche (hora del Pacífico).")
                elif 'token' in error_lower or 'auth' in error_lower:
                    st.info("💡 **Solución:** El token ha expirado. Regenera el token y actualiza los Secrets.")
                elif '400' in error_lower:
                    st.info("💡 **Solución:** Error en la solicitud. Verifica el formato del vídeo (MP4 recomendado).")


def render_drive_tab(drive_service, sheets_service, config, df, videos_drive):
    st.markdown("### 📁 Gestionar Google Drive")
    
    st.info("💡 Si subes vídeos directamente a Google Drive (sin usar esta app), aquí puedes añadirlos a la cola de procesamiento.")
    
    # Vídeos no registrados
    sheet_names = set(df['Nombre archivo'].str.lower())
    unregistered = [v for v in videos_drive if v['name'].lower() not in sheet_names]
    
    if unregistered:
        st.warning(f"⚠️ **{len(unregistered)} vídeo(s)** en Drive sin registrar en el sistema")
        
        if st.button("➕ Añadir todos al sistema", type="primary", use_container_width=True):
            for v in unregistered:
                add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'],
                                [v['name'], "", "", "Pendiente de rellenar", ""])
            st.success(f"✅ {len(unregistered)} vídeos añadidos. Ve a 'Rellenar datos' para completar la información.")
            time.sleep(1)
            st.rerun()
        
        st.divider()
        
        for v in unregistered:
            col1, col2 = st.columns([4, 1])
            with col1:
                size = int(v.get('size', 0)) / (1024 * 1024)
                st.write(f"📹 **{v['name']}** ({size:.1f} MB)")
            with col2:
                if st.button("➕ Añadir", key=f"add_{v['id']}"):
                    add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'],
                                    [v['name'], "", "", "Pendiente de rellenar", ""])
                    st.toast("✅ Añadido")
                    st.rerun()
    else:
        st.success("✅ **Todo sincronizado** - Todos los vídeos de Drive están registrados en el sistema")
    
    st.divider()
    
    # Resumen de carpetas
    st.markdown("#### 📂 Carpetas de Drive")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"📁 **/videos/**\n\n{len(videos_drive)} vídeo(s) pendientes")
    with col2:
        st.success(f"📁 **/procesados/**\n\nVídeos ya subidos a YouTube")
    with col3:
        st.error(f"📁 **/errores/**\n\nVídeos que fallaron")


def main():
    config = get_config()
    creds = get_credentials()
    
    if not config or not creds:
        st.error("⚠️ Configuración no encontrada. Configura los Secrets en Streamlit Cloud.")
        st.info("Necesitas configurar las credenciales de Google en los Secrets de la aplicación.")
        return
    
    # Servicios
    drive = get_drive_service(creds)
    sheets = get_sheets_service(creds)
    
    # Datos
    df = get_sheet_data(sheets, config['spreadsheet_id'], config['sheet_name'])
    videos_drive = list_videos_in_folder(drive, config['folder_videos'])
    
    # Contadores
    pendientes, en_cola, subidos, errores = get_counts(df)
    
    # Header con logo de YouTube + resumen
    st.markdown(f"""
    <div class="main-header">
        <div class="main-header-left">
            <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" alt="YouTube">
            <h1>Shorts Automation</h1>
        </div>
        <div class="main-header-right">
            <div class="stat-pill pending">📝 {pendientes} pendiente(s)</div>
            <div class="stat-pill queue">🚀 {en_cola} en cola</div>
            <div class="stat-pill done">✅ {subidos} subido(s)</div>
            {f'<div class="stat-pill error">❌ {errores} error(es)</div>' if errores > 0 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Notificación GLOBAL de videos recién subidos a YouTube
    if 'last_subidos_count' not in st.session_state:
        st.session_state.last_subidos_count = subidos
    
    if subidos > st.session_state.last_subidos_count:
        nuevos = subidos - st.session_state.last_subidos_count
        st.session_state.new_uploads_to_youtube = nuevos
        st.session_state.last_subidos_count = subidos
        
        # Notificación global visible en cualquier pestaña
        st.markdown(f"""
        <div class="global-notification">
            <div class="global-notification-icon">🎉</div>
            <div class="global-notification-text">
                <div class="global-notification-title">¡{nuevos} vídeo(s) nuevo(s) subido(s) a YouTube!</div>
                <div class="global-notification-subtitle">Revisa el historial para ver los enlaces de tus Shorts</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📤 Subir",
        f"✏️ Rellenar ({pendientes})" if pendientes > 0 else "✏️ Rellenar",
        f"🚀 En cola ({en_cola})" if en_cola > 0 else "🚀 En cola",
        f"📊 Historial ({subidos})" if subidos > 0 else "📊 Historial",
        f"📋 Logs ({errores})" if errores > 0 else "📋 Logs",
        "📁 Drive"
    ])
    
    with tab1:
        render_upload_tab(drive, sheets, config)
    
    with tab2:
        render_edit_tab(sheets, config, df)
    
    with tab3:
        render_queue_tab(df)
    
    with tab4:
        render_history_tab(df)
    
    with tab5:
        render_logs_tab(df)
    
    with tab6:
        render_drive_tab(drive, sheets, config, df, videos_drive)


if __name__ == "__main__":
    main()
