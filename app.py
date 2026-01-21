"""
YouTube Shorts Automation - Web App v12
- Sugerencias de IA con Gemini (generación instantánea al pulsar botón)
- Previsualización estilo YouTube
- Notificación global de subidas
"""

import streamlit as st
import pandas as pd
import os
import tempfile
import time
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import google.generativeai as genai

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
    @keyframes slideIn {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    .global-notification-icon { font-size: 2rem; }
    .global-notification-text { flex: 1; }
    .global-notification-title { font-weight: bold; font-size: 1.1rem; }
    .global-notification-subtitle { font-size: 0.9rem; opacity: 0.9; }
    
    .saved-message {
        background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        margin: 15px 0;
        font-weight: bold;
    }
    
    .ai-suggestion {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 15px 20px;
        margin: 10px 0;
        color: white;
    }
    .ai-suggestion-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
        font-weight: bold;
    }
    .ai-suggestion-title {
        background: rgba(255,255,255,0.2);
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .ai-suggestion-desc {
        background: rgba(255,255,255,0.1);
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 0.9rem;
    }
    .ai-suggestion-tags {
        margin-top: 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
    }
    .ai-tag {
        background: rgba(255,255,255,0.2);
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
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
            'gemini_api_key': st.secrets["google"]["gemini_api_key"],
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
        while len(row_data) < 7:
            row_data.append('')
        if not row_data[5]:
            row_data[5] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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

def download_file_from_drive(drive_service, file_id):
    try:
        request = drive_service.files().get_media(fileId=file_id)
        content = request.execute()
        return content
    except:
        return None

def find_file_in_drive(drive_service, filename, folder_id):
    try:
        query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        return files[0] if files else None
    except:
        return None

# ============== GEMINI ==============

def generate_suggestion_with_gemini(video_content, filename, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        ext = filename.lower().split('.')[-1]
        mime_types = {'mp4': 'video/mp4', 'mov': 'video/quicktime', 'avi': 'video/x-msvideo'}
        mime_type = mime_types.get(ext, 'video/mp4')
        
        prompt = """Analiza este vídeo corto (Short) y genera sugerencias en español.

IMPORTANTE: Responde SOLO con un JSON válido, sin texto adicional, sin markdown, sin ```json```.

El JSON debe tener exactamente esta estructura:
{"titulo": "título viral máximo 60 caracteres", "descripcion": "descripción atractiva con 3-5 hashtags relevantes al final, máximo 200 caracteres", "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]}

Reglas:
- El título debe ser llamativo, viral y generar curiosidad
- La descripción debe ser atractiva e incluir hashtags populares
- Los tags deben ser relevantes para YouTube Shorts
- Todo en español"""

        response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": video_content}
        ])
        
        response_text = response.text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        return json.loads(response_text)
    except Exception as e:
        st.error(f"Error con Gemini: {e}")
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
    return int((target - now).total_seconds())

def format_countdown(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}"

def get_counts(df):
    pendientes = len(df[(df['Título'].str.strip() == '') & (~df['Estado'].str.contains('Subido|Error|Borrado', case=False, na=False, regex=True))])
    en_cola = len(df[(df['Título'].str.strip() != '') & (~df['Estado'].str.contains('Subido|Error|Borrado', case=False, na=False, regex=True))])
    subidos = len(df[df['Estado'].str.contains('Subido', case=False, na=False)])
    errores = len(df[df['Estado'].str.contains('Error', case=False, na=False)])
    return pendientes, en_cola, subidos, errores

# ============== PÁGINAS ==============

def render_upload_tab(drive_service, sheets_service, config):
    st.markdown("### 📤 Subir vídeos a Drive")
    
    if st.session_state.get('just_uploaded', False):
        st.success("🎉 **¡Vídeos subidos correctamente!**")
        st.info("👉 Ve a la pestaña **'✏️ Rellenar'** para generar sugerencias con IA.")
        if st.button("📤 Subir más vídeos", type="primary"):
            st.session_state.just_uploaded = False
            st.rerun()
        return
    
    st.info("💡 Sube tus vídeos aquí. Luego genera títulos con IA en la pestaña 'Rellenar'.")
    
    files = st.file_uploader("Arrastra tus vídeos aquí", type=['mp4', 'mov', 'avi'], accept_multiple_files=True)
    
    if files:
        total_size = sum(f.size for f in files)
        st.write(f"📁 **{len(files)} vídeo(s)** - {format_size(total_size)}")
        
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


def render_edit_tab(drive_service, sheets_service, config, df):
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### ✏️ Rellenar títulos y descripciones")
    with col_refresh:
        if st.button("🔄 Actualizar", key="refresh_edit", use_container_width=True):
            st.rerun()
    
    sin_titulo = df[
        (df['Título'].str.strip() == '') & 
        (~df['Estado'].str.contains('Subido|Error|Borrado', case=False, na=False, regex=True))
    ].copy()
    
    if sin_titulo.empty:
        st.success("🎉 ¡Todo listo! No hay vídeos pendientes.")
        st.info("👉 Sube más vídeos en **'📤 Subir'** o revisa **'🚀 En cola'**")
        return
    
    st.warning(f"📝 **{len(sin_titulo)} vídeo(s)** pendientes. Pulsa ✨ para generar sugerencia con IA.")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        save_all = st.button("💾 Guardar todos", type="primary", use_container_width=True)
    with col3:
        delete_mode = st.checkbox("🗑️ Borrar", help="Modo borrar")
    
    st.divider()
    message_placeholder = st.empty()
    videos_data = {}
    saved_this_session = []
    
    for idx, row in sin_titulo.iterrows():
        st.markdown(f"""<div class="pending-card"><strong>📹 {row['Nombre archivo']}</strong></div>""", unsafe_allow_html=True)
        
        # Session state para sugerencias
        suggestion_key = f"suggestion_{idx}"
        if suggestion_key not in st.session_state:
            st.session_state[suggestion_key] = None
        
        suggestion = st.session_state[suggestion_key]
        
        # Mostrar sugerencia si existe
        if suggestion:
            st.markdown(f"""
            <div class="ai-suggestion">
                <div class="ai-suggestion-header">✨ Sugerencia de Gemini</div>
                <div class="ai-suggestion-title">📌 {suggestion.get('titulo', '')}</div>
                <div class="ai-suggestion-desc">📝 {suggestion.get('descripcion', '')}</div>
                <div class="ai-suggestion-tags">{''.join([f'<span class="ai-tag">#{tag}</span>' for tag in suggestion.get('tags', [])])}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Inputs
        if delete_mode:
            col_t, col_d, col_del = st.columns([3, 2.5, 1])
        else:
            col_t, col_d, col_ai, col_use, col_save = st.columns([2.5, 2, 0.7, 0.7, 0.7])
        
        titulo_key = f"titulo_{idx}"
        desc_key = f"desc_{idx}"
        
        with col_t:
            titulo = st.text_input("Título", key=f"t_{idx}", value=st.session_state.get(titulo_key, ""), placeholder="Título del Short...", label_visibility="collapsed")
        
        with col_d:
            desc = st.text_input("Descripción", key=f"d_{idx}", value=st.session_state.get(desc_key, ""), placeholder="Descripción...", label_visibility="collapsed")
        
        if delete_mode:
            with col_del:
                if st.button("🗑️", key=f"del_{idx}", use_container_width=True):
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=config['spreadsheet_id'],
                        range=f"'{config['sheet_name']}'!D{idx + 2}",
                        valueInputOption="RAW",
                        body={"values": [["Borrado"]]}
                    ).execute()
                    st.toast("🗑️ Borrado")
        else:
            with col_ai:
                if st.button("✨", key=f"ai_{idx}", help="Generar con IA", use_container_width=True):
                    with st.spinner("🤖 Analizando..."):
                        file_info = find_file_in_drive(drive_service, row['Nombre archivo'], config['folder_videos'])
                        if file_info:
                            video_content = download_file_from_drive(drive_service, file_info['id'])
                            if video_content:
                                result = generate_suggestion_with_gemini(video_content, row['Nombre archivo'], config['gemini_api_key'])
                                if result:
                                    st.session_state[suggestion_key] = result
                                    st.rerun()
            
            with col_use:
                if suggestion:
                    if st.button("📋", key=f"use_{idx}", help="Usar sugerencia", use_container_width=True):
                        st.session_state[titulo_key] = suggestion.get('titulo', '')
                        st.session_state[desc_key] = suggestion.get('descripcion', '')
                        st.rerun()
            
            with col_save:
                if st.button("💾", key=f"s_{idx}", help="Guardar", use_container_width=True):
                    if titulo.strip():
                        if update_sheet_row(sheets_service, config['spreadsheet_id'], config['sheet_name'], idx + 2, titulo, desc):
                            saved_this_session.append(row['Nombre archivo'])
                            st.session_state[suggestion_key] = None
                    else:
                        st.toast("⚠️ Título obligatorio")
        
        videos_data[idx] = {'titulo': titulo, 'desc': desc}
        st.write("")
    
    if saved_this_session:
        message_placeholder.markdown(f"""<div class="saved-message">✅ ¡{len(saved_this_session)} guardado(s)! Pulsa Actualizar.</div>""", unsafe_allow_html=True)
    
    if save_all:
        valid = {k: v for k, v in videos_data.items() if v['titulo'].strip()}
        if valid:
            saved = sum(1 for idx, data in valid.items() if update_sheet_row(sheets_service, config['spreadsheet_id'], config['sheet_name'], idx + 2, data['titulo'], data['desc']))
            if saved:
                message_placeholder.markdown(f"""<div class="saved-message">✅ ¡{saved} guardado(s)!</div>""", unsafe_allow_html=True)


def render_queue_tab(df):
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### 🚀 En cola")
    with col_refresh:
        if st.button("🔄 Actualizar", key="refresh_queue", use_container_width=True):
            st.rerun()
    
    seconds_left = get_next_process_time()
    en_cola = df[(df['Título'].str.strip() != '') & (~df['Estado'].str.contains('Subido|Error|Borrado', case=False, na=False, regex=True))].copy()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="stats-box"><div class="stats-number">⏱️ {format_countdown(seconds_left)}</div><div class="stats-label">Próximo proceso</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="stats-box"><div class="stats-number">{len(en_cola)}</div><div class="stats-label">En cola</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="stats-box"><div class="stats-number">5 min</div><div class="stats-label">Intervalo</div></div>""", unsafe_allow_html=True)
    
    st.write("")
    
    if en_cola.empty:
        st.info("📭 No hay vídeos en cola.")
        return
    
    st.success(f"🎬 **{len(en_cola)} vídeo(s)** listos")
    st.divider()
    
    for idx, row in en_cola.iterrows():
        st.markdown(f"""
        <div class="queue-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="queue-card-title">🎬 {row['Título']}</div>
                    <div class="queue-card-file">📁 {row['Nombre archivo']}</div>
                </div>
                <div class="queue-card-time">⏳ {format_countdown(seconds_left)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_history_tab(df):
    st.markdown("### 📊 Historial")
    done_df = df[df['Estado'].str.contains('Subido', case=False, na=False)].copy()
    
    if done_df.empty:
        st.info("📭 No hay vídeos publicados aún.")
        return
    
    st.success(f"🎬 **{len(done_df)} Short(s)** publicados")
    st.divider()
    
    for idx, row in done_df.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{row['Título']}**")
            st.caption(f"📁 {row['Nombre archivo']}")
        with col2:
            if row['YouTube URL']:
                st.link_button("▶️ Ver", row['YouTube URL'], use_container_width=True)
        st.divider()


def render_logs_tab(df):
    st.markdown("### 📋 Logs")
    pendientes, en_cola, subidos, errores = get_counts(df)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📝 Pendientes", pendientes)
    col2.metric("🚀 Cola", en_cola)
    col3.metric("✅ Subidos", subidos)
    col4.metric("❌ Errores", errores)
    
    st.divider()
    error_df = df[df['Estado'].str.contains('Error', case=False, na=False)]
    
    if error_df.empty:
        st.success("✅ Sin errores")
    else:
        st.error(f"⚠️ {len(error_df)} error(es)")
        for idx, row in error_df.iterrows():
            with st.expander(f"❌ {row['Nombre archivo']}"):
                st.code(row['Estado'])


def render_drive_tab(drive_service, sheets_service, config, df, videos_drive):
    st.markdown("### 📁 Drive")
    sheet_names = set(df['Nombre archivo'].str.lower())
    unregistered = [v for v in videos_drive if v['name'].lower() not in sheet_names]
    
    if unregistered:
        st.warning(f"⚠️ **{len(unregistered)}** sin registrar")
        if st.button("➕ Añadir todos", type="primary", use_container_width=True):
            for v in unregistered:
                add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], [v['name'], "", "", "Pendiente de rellenar", ""])
            st.rerun()
    else:
        st.success("✅ Todo sincronizado")


def main():
    config = get_config()
    creds = get_credentials()
    
    if not config or not creds:
        st.error("⚠️ Configuración no encontrada.")
        return
    
    drive = get_drive_service(creds)
    sheets = get_sheets_service(creds)
    df = get_sheet_data(sheets, config['spreadsheet_id'], config['sheet_name'])
    videos_drive = list_videos_in_folder(drive, config['folder_videos'])
    pendientes, en_cola, subidos, errores = get_counts(df)
    
    st.markdown(f"""
    <div class="main-header">
        <div class="main-header-left">
            <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" alt="YouTube">
            <h1>Shorts Automation</h1>
        </div>
        <div class="main-header-right">
            <div class="stat-pill pending">📝 {pendientes}</div>
            <div class="stat-pill queue">🚀 {en_cola}</div>
            <div class="stat-pill done">✅ {subidos}</div>
            {f'<div class="stat-pill error">❌ {errores}</div>' if errores else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📤 Subir",
        f"✏️ Rellenar ({pendientes})" if pendientes else "✏️ Rellenar",
        f"🚀 Cola ({en_cola})" if en_cola else "🚀 Cola",
        f"📊 Historial ({subidos})" if subidos else "📊 Historial",
        "📋 Logs",
        "📁 Drive"
    ])
    
    with tab1:
        render_upload_tab(drive, sheets, config)
    with tab2:
        render_edit_tab(drive, sheets, config, df)
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
