import requests
import gspread
from google.oauth2.service_account import Credentials
import os
import time
from datetime import datetime
from dotenv import load_dotenv

print("🕵️ Iniciando Auditoría Creativa: Escaneando últimos 50 posts...")

# Cargamos la bóveda de seguridad
load_dotenv()

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_json = os.path.join(ruta_actual, 'credenciales_google.json')
credenciales = Credentials.from_service_account_file(ruta_json, scopes=scopes)
cliente = gspread.authorize(credenciales)

# ⚠️ PEGA AQUÍ LA URL DEL NUEVO EXCEL DE LA FÁBRICA
url_excel = 'https://docs.google.com/spreadsheets/d/1qdYoi0NrtW-tr_gNboY6rbOHf_u05tbiYsAANcF4BJY/edit'
hoja_calculo = cliente.open_by_url(url_excel)
pestana = hoja_calculo.worksheet('Auditoria_Creativos')

# --- 2. CREDENCIALES DE META API (Cuenta Textil) ---
ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
IG_USER_ID = os.getenv('IG_USER_ID')

# --- 3. EXTRACCIÓN DEL CATÁLOGO DE POSTS ---
url_media = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
params_media = {
    'fields': 'id,timestamp,media_type,permalink,like_count,comments_count',
    'limit': 50,
    'access_token': ACCESS_TOKEN
}

respuesta = requests.get(url_media, params=params_media).json()
filas_para_excel = []

if 'data' in respuesta:
    posts = respuesta['data']
    print(f"✅ Se encontraron {len(posts)} publicaciones. Analizando una por una...")
    
    for i, post in enumerate(posts):
        print(f"⏳ Escaneando post {i+1} de {len(posts)}...")
        post_id = post['id']
        formato = post.get('media_type', 'UNKNOWN')
        link = post.get('permalink', '')
        likes = post.get('like_count', 0)
        comentarios = post.get('comments_count', 0)
        
        # Limpiamos la fecha
        fecha_sucia = post['timestamp']
        fecha_limpia = datetime.strptime(fecha_sucia[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
        
        # --- 4. EXTRACCIÓN DE INSIGHTS PRIVADOS (Alcance y Guardados) ---
        url_insights = f"https://graph.facebook.com/v19.0/{post_id}/insights"
        
        if formato == 'VIDEO':
            metricas_pedir = 'reach,saved' 
        else:
            metricas_pedir = 'reach,saved'
            
        params_insights = {
            'metric': metricas_pedir,
            'access_token': ACCESS_TOKEN
        }
        
        try:
            res_insights = requests.get(url_insights, params=params_insights).json()
            alcance = 0
            guardados = 0
            
            if 'data' in res_insights:
                for insight in res_insights['data']:
                    if insight['name'] == 'reach':
                        alcance = insight['values'][0]['value']
                    elif insight['name'] == 'saved':
                        guardados = insight['values'][0]['value']
            
            # Guardamos la fila
            filas_para_excel.append([fecha_limpia, formato, alcance, likes, comentarios, guardados, link])
            
        except Exception as e:
            print(f"⚠️ Error sacando insights del post {post_id}: {e}")
            
        # 🛡️ Escudo Anti-Bloqueos (Meta es estricto cuando pides post por post)
        time.sleep(1) 

else:
    print("❌ Error trayendo los posts principales. Revisa el Token.")
    print(respuesta)

# --- 5. INYECCIÓN EN GOOGLE SHEETS ---
if filas_para_excel:
    print("💾 Borrando datos viejos e inyectando reporte fresco...")
    # Limpiamos la hoja (dejando la fila 1 de encabezados)
    pestana.resize(1) 
    pestana.append_rows(filas_para_excel)
    print("🎉 ¡Auditoría completada! Revisa tu Excel.")