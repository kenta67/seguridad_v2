import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')
from app.config import settings
import requests

token = settings.whatsapp_access_token
phone_id = settings.whatsapp_phone_number_id
# numero del destinatario con codigo de pais
phone = "59169941968"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}
base_url = f"https://graph.facebook.com/{settings.whatsapp_graph_version}/{phone_id}/messages"

print("=== Test 1: Plantilla hello_world ===")
r = requests.post(base_url, headers=headers, json={
    "messaging_product": "whatsapp",
    "to": phone,
    "type": "template",
    "template": {"name": "hello_world", "language": {"code": "en_US"}},
}, timeout=15)
print(f"HTTP {r.status_code}: {r.text[:300]}")

print()
print("=== Test 2: Mensaje de texto personalizado ===")
r2 = requests.post(base_url, headers=headers, json={
    "messaging_product": "whatsapp",
    "to": phone,
    "type": "text",
    "text": {"body": "🔴 ALERTA ROJA - Mensaje de prueba personalizado"},
}, timeout=15)
print(f"HTTP {r2.status_code}: {r2.text[:500]}")
