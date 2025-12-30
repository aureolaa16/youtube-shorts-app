"""
YouTube Shorts Automation - Web App v7
- Logs y errores detallados
- Sincronización clara
- Flujo intuitivo
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
from googleapiclient.http import MediaFileUpload

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
    /* General */
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
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
        flex-wrap: wrap;
        gap: 10px;
    }
    .workflow-step {
        text-align: center;
        flex: 1;
        min-width: 120px;
        padding: 10px;
    }
    .workflow-step-icon {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 8px;
        font-size: 1.3rem;
    }
    .step-active .workflow-step-icon {
        background: linear-gradient(135deg, #1a73e8, #0d47a1);
        color: white;
        box-shadow: 0 4px 15px rgba(26, 115, 232, 0.4);
    }
    .step-done .workflow-step-icon {
        background: linear-gradient(135deg, #4caf50, #2e7d32);
        color: white;
    }
    .step-pending .workflow-step-icon {
        background: #e0e0e0;
        color: #999;
    }
    .step-error .workflow-step-icon {
        background: linear-gradient(135deg, #f44336, #c62828);
        color: white;
    }
    .workflow-step-title {
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 3px;
    }
    .workflow-step-count {
        font-size: 0.75rem;
        color: #666;
    }
    .workflow-arrow {
        color: #ccc;
        font-size: 1.2rem;
    }
    
    /* Cards */
    .card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 15px;
    }
    .card-blue { border-left: 4px solid #1a73e8; }
    .card-green { border-left: 4px solid #4caf50; }
    .card-orange { border-left: 4px solid #ff9800; }
    .card-red { border-left: 4px solid #f44336; }
    .card-gray { border-left: 4px solid #9e9e9e; }
    
    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .badge-pending { background: #fff3e0; color: #e65100; }
    .badge-ready { background: #e3f2fd; color: #1565c0; }
    .badge-done { background: #e8f5e9; color: #2e7d32; }
    .badge-error { background: #ffebee; color: #c62828; }
    .badge-processing { background: #f3e5f5; color: #7b1fa2; }
    
    /* Info boxes */
    .info-box {
        padding: 15px 20px;
        border-radius: 10px;
        margin: 15px 0;
    }
    .info-blue { background: #e3f2fd; border-left: 4px solid #1976d2; }
    .info-green { background: #e8f5e9; border-left: 4px solid #4caf50; }
    .info-orange { background: #fff3e0; border-left: 4px solid #ff9800; }
    .info-red { background: #ffebee; border-left: 4px solid #f44336; }
    
    /* Video item */
    .video-item {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #eee;
        transition: all 0.2s;
    }
    .video-item:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Metrics */
    .metric {
        text-align: center;
        padding: 15px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #666;
        margin-top: 5px;
    }
    
    /* Log entry */
    .log-entry {
        padding: 12px 15px;
        border-radius: 8px;
        margin: 8px 0;
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .log-success { background: #e8f5e9; }
    .log-error { background: #ffebee; }
    .log-warning { background: #fff3e0; }
    .log-info { background: #e3f2fd; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        background: #f5f5f5;
        padding: 5px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
    }
    .stTabs [aria-selected="true"] {
        background: white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 40px;
        background: #fafafa;
        border-radius: 12px;
        border: 2px dashed #ddd;
    }
    .empty-icon { font-size: 3rem; margin-bottom: 10px; }
    
    /* Character counter */
    .char-count {
        font-size: 0.75rem;
        text-align: right;
        margin-top: 3px;
    }
    .char-ok { color: #4caf50; }
    .char-warn { color: #ff9800; }
    .char-bad { color: #f44336; }
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
    except:
        return pd.DataFrame(columns=['Nombre archivo', 'Título', 'Descripción', 'Estado', 'YouTube URL'])

def add_row_to_sheet(sheets_service, spreadsheet_id, sheet_name, row_data):
    try:
        sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A:E",
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
                remaining = ((1 - status.progress()) * elapsed / status.progress()) if status.progress() > 0 else 0
                progress_cb(status.progress(), speed, remaining)
        
        os.unlink(tmp_path)
        return response
    except Exception as e:
        return None


# ============== HELPERS ==============

def format_size(b):
    if b < 1024: return f"{b} B"
    if b < 1024**2: return f"{b/1024:.1f} KB"
    return f"{b/1024**2:.1f} MB"

def format_time(s):
    if s < 60: return f"{s:.0f}s"
    return f"{s/60:.1f}min"

def get_next_process():
    now = datetime.now()
    next_5 = ((now.minute // 5) + 1) * 5
    if next_5 >= 60:
        target = now.replace(minute=0, second=0) + timedelta(hours=1)
    else:
        target = now.replace(minute=next_5, second=0)
    return (target - now).seconds

def get_counts(df):
    pending = len(df[(df['Título'].str.strip() == '') | df['Estado'].str.contains('Pendiente', case=False, na=True)])
    ready = len(df[(df['Título'].str.strip() != '') & ~df['Estado'].str.contains('Subido|Error', case=False, na=False, regex=True)])
    done = len(df[df['Estado'].str.contains('Subido', case=False, na=False)])
    errors = len(df[df['Estado'].str.contains('Error', case=False, na=False)])
    return pending, ready, done, errors


# ============== UI COMPONENTS ==============

def render_workflow(df, videos_drive):
    pending, ready, done, errors = get_counts(df)
    
    # Determinar estado activo
    if len(videos_drive) == 0 and len(df) == 0:
        active = 1
    elif pending > 0:
        active = 2
    elif ready > 0:
        active = 3
    else:
        active = 4
    
    def step_class(n, count, is_error=False):
        if is_error and count > 0:
            return "step-error"
        if n < active or count > 0 and n == 4:
            return "step-done"
        if n == active:
            return "step-active"
        return "step-pending"
    
    st.markdown(f"""
    <div class="workflow-container">
        <div class="workflow-step {step_class(1, len(videos_drive))}">
            <div class="workflow-step-icon">📤</div>
            <div class="workflow-step-title">1. Subir</div>
            <div class="workflow-step-count">{len(videos_drive)} en Drive</div>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step {step_class(2, pending)}">
            <div class="workflow-step-icon">✏️</div>
            <div class="workflow-step-title">2. Rellenar</div>
            <div class="workflow-step-count">{pending} sin título</div>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step {step_class(3, ready)}">
            <div class="workflow-step-icon">⏳</div>
            <div class="workflow-step-title">3. En cola</div>
            <div class="workflow-step-count">{ready} listos</div>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step {step_class(4, done)}">
            <div class="workflow-step-icon">✅</div>
            <div class="workflow-step-title">4. Publicado</div>
            <div class="workflow-step-count">{done} en YouTube</div>
        </div>
        {f'<div class="workflow-arrow">⚠️</div><div class="workflow-step step-error"><div class="workflow-step-icon">❌</div><div class="workflow-step-title">Errores</div><div class="workflow-step-count">{errors} fallidos</div></div>' if errors > 0 else ''}
    </div>
    """, unsafe_allow_html=True)


def render_upload_tab(drive_service, sheets_service, config):
    st.markdown("### 📤 Subir vídeos")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        <div class="info-box info-blue">
            <strong>💡 ¿Cómo funciona?</strong><br>
            <small>Sube tus vídeos aquí → Se guardan en Google Drive → Después añades título en la pestaña "Rellenar datos"</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-box info-green">
            <strong>📋 Requisitos</strong><br>
            <small>• Vertical 9:16<br>• Máx 60 seg<br>• MP4/MOV/AVI</small>
        </div>
        """, unsafe_allow_html=True)
    
    files = st.file_uploader("Arrastra tus vídeos aquí", type=['mp4', 'mov', 'avi'], accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        total_size = sum(f.size for f in files)
        est_time = total_size / (1024 * 1024) * 2  # ~2s por MB
        
        st.markdown(f"""
        <div class="card card-blue">
            <strong>{len(files)} vídeo(s)</strong> · {format_size(total_size)} · ~{format_time(est_time)} de subida
        </div>
        """, unsafe_allow_html=True)
        
        for f in files:
            st.markdown(f"📹 **{f.name}** ({format_size(f.size)})")
        
        if st.button("🚀 Subir a Drive", type="primary", use_container_width=True):
            progress = st.progress(0)
            
            for i, f in enumerate(files):
                status = st.empty()
                file_progress = st.progress(0)
                
                status.markdown(f"⏳ Subiendo **{f.name}**...")
                
                def update(p, speed, rem):
                    file_progress.progress(p)
                
                result = upload_video_to_drive(drive_service, config['folder_videos'], f, f.name, update)
                
                if result:
                    add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'], 
                                    [f.name, "", "", "Pendiente de rellenar", ""])
                    status.markdown(f"✅ **{f.name}** subido")
                else:
                    status.markdown(f"❌ **{f.name}** falló")
                
                file_progress.empty()
                progress.progress((i + 1) / len(files))
            
            st.success("🎉 ¡Subida completada! Ahora ve a **'✏️ Rellenar datos'** para añadir títulos.")
            st.balloons()


def render_edit_tab(sheets_service, config, df):
    st.markdown("### ✏️ Rellenar títulos y descripciones")
    
    # Timer
    next_proc = get_next_process()
    st.markdown(f"""
    <div class="info-box info-blue">
        ⏱️ <strong>Próximo procesamiento:</strong> {next_proc // 60}:{next_proc % 60:02d} min
    </div>
    """, unsafe_allow_html=True)
    
    # Filtrar pendientes (sin título o estado pendiente)
    pending_df = df[
        (df['Título'].str.strip() == '') | 
        df['Estado'].str.contains('Pendiente', case=False, na=True) |
        (df['Estado'] == '')
    ].copy()
    
    if pending_df.empty:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🎉</div>
            <h3>¡Todo listo!</h3>
            <p>No hay vídeos pendientes. Sube más en la pestaña anterior.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Header con contador y botón guardar todos
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{len(pending_df)} vídeo(s) pendiente(s) de título**")
    with col2:
        save_all = st.button("💾 Guardar todos", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # Recopilar datos
    videos_data = {}
    
    for idx, row in pending_df.iterrows():
        col_name, col_title, col_desc, col_preview, col_btn = st.columns([2, 2.5, 2.5, 0.5, 0.5])
        
        with col_name:
            st.markdown(f"📹 **{row['Nombre archivo'][:20]}{'...' if len(row['Nombre archivo']) > 20 else ''}**")
        
        with col_title:
            titulo = st.text_input("Título", key=f"t_{idx}", placeholder="Título del Short...", label_visibility="collapsed")
        
        with col_desc:
            desc = st.text_input("Descripción", key=f"d_{idx}", placeholder="Descripción (opcional)", label_visibility="collapsed")
        
        with col_preview:
            preview = st.checkbox("👁️", key=f"p_{idx}", help="Previsualizar")
        
        with col_btn:
            if st.button("✓", key=f"s_{idx}", help="Guardar este vídeo"):
                if titulo.strip():
                    if update_sheet_row(sheets_service, config['spreadsheet_id'], config['sheet_name'], idx + 2, titulo, desc):
                        st.toast(f"✅ Guardado")
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.toast("❌ Error")
                else:
                    st.toast("⚠️ Falta título")
        
        # Previsualización si está activada
        if preview:
            st.markdown(f"""
            <div style="background: #000; color: #fff; padding: 15px; border-radius: 10px; max-width: 280px; margin: 10px 0 15px 0;">
                <div style="background: #222; height: 300px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px;">
                    <span style="font-size: 2.5rem;">📹</span>
                </div>
                <div style="font-weight: bold; font-size: 0.9rem; margin-bottom: 5px;">
                    {titulo if titulo else '<span style="color: #666;">Sin título...</span>'}
                </div>
                <div style="font-size: 0.8rem; color: #aaa;">
                    {desc[:100] + '...' if len(desc) > 100 else desc if desc else '<span style="color: #555;">Sin descripción...</span>'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        videos_data[idx] = {'titulo': titulo, 'desc': desc}
    
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
            
            st.success(f"✅ {saved} vídeo(s) guardado(s)")
            time.sleep(0.5)
            st.rerun()


def render_history_tab(df):
    st.markdown("### 📊 Vídeos publicados en YouTube")
    
    done_df = df[df['Estado'].str.contains('Subido', case=False, na=False)]
    
    if done_df.empty:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <h3>Aún no hay vídeos publicados</h3>
            <p>Aparecerán aquí cuando se suban a YouTube</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"""
    <div class="info-box info-green">
        <strong>🎬 {len(done_df)} Short(s) publicado(s)</strong>
    </div>
    """, unsafe_allow_html=True)
    
    for _, row in done_df.iterrows():
        st.markdown(f"""
        <div class="card card-green">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <strong style="font-size: 1.1rem;">{row['Título']}</strong>
                    <div style="color: #666; font-size: 0.85rem; margin-top: 5px;">📁 {row['Nombre archivo']}</div>
                    <div style="color: #888; font-size: 0.85rem;">{row['Descripción'][:80]}{'...' if len(row['Descripción']) > 80 else ''}</div>
                </div>
                <span class="badge badge-done">✅ Publicado</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if row['YouTube URL']:
            st.link_button("▶️ Ver en YouTube", row['YouTube URL'])
        st.markdown("")


def render_logs_tab(df, drive_service, config):
    st.markdown("### 📋 Logs, Errores y Estado")
    
    # === ERRORES ===
    st.markdown("#### ❌ Vídeos con errores")
    
    error_df = df[df['Estado'].str.contains('Error', case=False, na=False)]
    
    if error_df.empty:
        st.markdown("""
        <div class="info-box info-green">
            ✅ <strong>Sin errores</strong> - Todos los vídeos se han procesado correctamente
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="info-box info-red">
            ⚠️ <strong>{len(error_df)} vídeo(s) con error</strong>
        </div>
        """, unsafe_allow_html=True)
        
        for idx, row in error_df.iterrows():
            error_msg = row['Estado']
            
            # Detectar tipo de error
            if 'uploadLimitExceeded' in error_msg or 'exceeded' in error_msg.lower():
                error_type = "🚫 Límite diario de YouTube"
                solution = "Has subido demasiados vídeos hoy. Espera 24 horas."
                icon = "🕐"
            elif 'quota' in error_msg.lower():
                error_type = "📊 Cuota de API agotada"
                solution = "La cuota se resetea a medianoche (hora del Pacífico)."
                icon = "📉"
            elif 'token' in error_msg.lower() or 'auth' in error_msg.lower() or 'credential' in error_msg.lower():
                error_type = "🔐 Error de autenticación"
                solution = "Regenera el token y actualiza los Secrets en Streamlit."
                icon = "🔑"
            else:
                error_type = "❓ Error desconocido"
                solution = "Revisa los detalles del error abajo."
                icon = "🔍"
            
            st.markdown(f"""
            <div class="card card-red">
                <div style="margin-bottom: 10px;">
                    <span class="badge badge-error">{error_type}</span>
                    <strong style="margin-left: 10px;">📹 {row['Nombre archivo']}</strong>
                </div>
                <div style="background: #fff5f5; padding: 10px; border-radius: 8px; margin: 10px 0;">
                    <strong>{icon} Solución:</strong> {solution}
                </div>
                <details>
                    <summary style="cursor: pointer; color: #666; font-size: 0.85rem;">Ver error técnico</summary>
                    <code style="display: block; background: #f5f5f5; padding: 10px; margin-top: 10px; border-radius: 5px; font-size: 0.75rem; word-break: break-all;">
                        {error_msg}
                    </code>
                </details>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === ESTADO DEL SISTEMA ===
    st.markdown("#### 🔧 Estado del sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    
    pending, ready, done, errors = get_counts(df)
    
    with col1:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value" style="color: #1a73e8;">{len(df)}</div>
            <div class="metric-label">Total registrados</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value" style="color: #ff9800;">{pending}</div>
            <div class="metric-label">Sin título</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value" style="color: #4caf50;">{done}</div>
            <div class="metric-label">Publicados</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value" style="color: #f44336;">{errors}</div>
            <div class="metric-label">Con errores</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === VÍDEOS EN CARPETA DE ERRORES ===
    st.markdown("#### 📁 Vídeos en carpeta de errores (Drive)")
    
    try:
        error_videos = list_videos_in_folder(drive_service, config['folder_errores'])
        if error_videos:
            st.warning(f"Hay {len(error_videos)} vídeo(s) en la carpeta de errores de Drive")
            for v in error_videos:
                st.markdown(f"- 📹 {v['name']}")
            st.info("💡 Para reintentar: mueve el vídeo de `/errores/` a `/videos/` en Drive")
        else:
            st.success("✅ La carpeta de errores está vacía")
    except:
        st.info("No se pudo acceder a la carpeta de errores")
    
    st.markdown("---")
    
    # === ACTIVIDAD RECIENTE ===
    st.markdown("#### 📜 Resumen de actividad")
    
    # Mostrar últimos vídeos procesados
    if done > 0:
        st.markdown("**Últimos publicados:**")
        for _, row in df[df['Estado'].str.contains('Subido', case=False, na=False)].tail(5).iterrows():
            st.markdown(f"""
            <div class="log-entry log-success">
                ✅ <strong>{row['Título']}</strong> publicado en YouTube
            </div>
            """, unsafe_allow_html=True)
    
    if errors > 0:
        st.markdown("**Últimos errores:**")
        for _, row in error_df.tail(3).iterrows():
            st.markdown(f"""
            <div class="log-entry log-error">
                ❌ <strong>{row['Nombre archivo']}</strong> falló
            </div>
            """, unsafe_allow_html=True)


def render_drive_tab(drive_service, sheets_service, config, df, videos_drive):
    st.markdown("### 📁 Gestionar vídeos en Drive")
    
    st.markdown("""
    <div class="info-box info-blue">
        <strong>💡 ¿Para qué sirve esto?</strong><br>
        <small>Si subes vídeos directamente a Google Drive (sin usar esta app), aquí puedes añadirlos a la cola de procesamiento.</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Vídeos en Drive no registrados
    sheet_names = set(df['Nombre archivo'].str.lower())
    unregistered = [v for v in videos_drive if v['name'].lower() not in sheet_names]
    
    st.markdown("#### 📥 Vídeos en Drive pendientes de registrar")
    
    if unregistered:
        st.markdown(f"""
        <div class="info-box info-orange">
            <strong>⚠️ {len(unregistered)} vídeo(s) sin registrar</strong><br>
            <small>Estos vídeos están en Drive pero no aparecen en la cola. Añádelos para poder ponerles título.</small>
        </div>
        """, unsafe_allow_html=True)
        
        for v in unregistered:
            col1, col2 = st.columns([4, 1])
            with col1:
                size = int(v.get('size', 0)) / (1024 * 1024)
                st.markdown(f"📹 **{v['name']}** ({size:.1f} MB)")
            with col2:
                if st.button("➕ Añadir", key=f"add_{v['id']}"):
                    add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'],
                                    [v['name'], "", "", "Pendiente de rellenar", ""])
                    st.toast("✅ Añadido a la cola")
                    st.rerun()
        
        st.markdown("")
        if st.button("➕ Añadir todos a la cola", type="primary"):
            for v in unregistered:
                add_row_to_sheet(sheets_service, config['spreadsheet_id'], config['sheet_name'],
                                [v['name'], "", "", "Pendiente de rellenar", ""])
            st.toast(f"✅ {len(unregistered)} vídeos añadidos")
            st.rerun()
    else:
        st.markdown("""
        <div class="info-box info-green">
            ✅ <strong>Todo sincronizado</strong> - Todos los vídeos de Drive están en la cola
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Resumen de carpetas
    st.markdown("#### 📊 Resumen de carpetas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="card card-blue">
            <strong>📥 /videos/</strong><br>
            <span style="font-size: 1.5rem; font-weight: bold;">{len(videos_drive)}</span> vídeos
            <br><small style="color: #666;">Pendientes de procesar</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        try:
            procesados = list_videos_in_folder(drive_service, config['folder_procesados'])
            count_proc = len(procesados)
        except:
            count_proc = "?"
        st.markdown(f"""
        <div class="card card-green">
            <strong>✅ /procesados/</strong><br>
            <span style="font-size: 1.5rem; font-weight: bold;">{count_proc}</span> vídeos
            <br><small style="color: #666;">Ya subidos a YouTube</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        try:
            errores = list_videos_in_folder(drive_service, config['folder_errores'])
            count_err = len(errores)
        except:
            count_err = "?"
        st.markdown(f"""
        <div class="card card-red">
            <strong>❌ /errores/</strong><br>
            <span style="font-size: 1.5rem; font-weight: bold;">{count_err}</span> vídeos
            <br><small style="color: #666;">Fallaron al subir</small>
        </div>
        """, unsafe_allow_html=True)


def render_help():
    with st.expander("❓ Ayuda y preguntas frecuentes"):
        st.markdown("""
        ### ¿Cómo funciona el sistema?
        
        1. **Subes vídeos** → Se guardan en Google Drive
        2. **Añades título** → El vídeo queda listo para procesar
        3. **Cada 5 minutos** → El sistema sube automáticamente a YouTube
        4. **Recibes email** → Confirmación con el enlace del Short
        
        ---
        
        ### Preguntas frecuentes
        
        **¿Por qué mi vídeo no se sube?**
        - Verifica que tiene título (pestaña "Rellenar datos")
        - Revisa si hay errores (pestaña "Logs y errores")
        - Puede ser límite diario de YouTube
        
        **¿Puedo subir vídeos directo a Drive?**
        - Sí, después ve a "Gestionar Drive" y añádelos a la cola
        
        **¿Qué pasa si hay un error?**
        - El vídeo se mueve a la carpeta /errores/
        - Revisa el error en "Logs y errores"
        - Para reintentar: mueve el vídeo de /errores/ a /videos/ en Drive
        
        **¿Cuál es el límite de YouTube?**
        - Las cuentas nuevas tienen límite diario (~5-10 vídeos)
        - Verificar el canal aumenta el límite
        - El límite se resetea cada 24 horas
        """)


def main():
    config = get_config()
    creds = get_credentials()
    
    if not config or not creds:
        st.error("⚠️ Configuración no encontrada")
        st.info("Configura los Secrets en Streamlit Cloud: Settings → Secrets")
        return
    
    # Header
    st.markdown('<p class="main-header">🎬 YouTube Shorts Automation</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sube, edita y publica tus Shorts automáticamente</p>', unsafe_allow_html=True)
    
    # Servicios
    drive = get_drive_service(creds)
    sheets = get_sheets_service(creds)
    
    # Datos
    df = get_sheet_data(sheets, config['spreadsheet_id'], config['sheet_name'])
    videos_drive = list_videos_in_folder(drive, config['folder_videos'])
    
    # Workflow
    render_workflow(df, videos_drive)
    
    # Tabs
    tabs = st.tabs([
        "📤 Subir vídeos",
        "✏️ Rellenar datos",
        "📊 Historial",
        "📋 Logs y errores",
        "📁 Gestionar Drive"
    ])
    
    with tabs[0]:
        render_upload_tab(drive, sheets, config)
    
    with tabs[1]:
        render_edit_tab(sheets, config, df)
    
    with tabs[2]:
        render_history_tab(df)
    
    with tabs[3]:
        render_logs_tab(df, drive, config)
    
    with tabs[4]:
        render_drive_tab(drive, sheets, config, df, videos_drive)
    
    # Help
    render_help()
    
    # Footer
    st.markdown("---")
    st.caption(f"📧 {config['notification_email']} | ⏱️ Procesamiento cada 5 min | 🔄 Recarga para actualizar")


if __name__ == "__main__":
    main()
