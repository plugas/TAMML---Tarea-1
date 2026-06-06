# Qué debe pasarte tu compañero (Meta + WhatsApp)

Usa este documento como checklist. **No subir nada de esto a GitHub.**

---

## 1. Datos obligatorios (para tu `.env` y N8N)

| Dato | Dónde lo ve en Meta | Ejemplo | Para qué |
|------|-------------------|---------|----------|
| **Phone number ID** | WhatsApp → API Setup | `123456789012345` | Enviar respuestas por Graph API |
| **Temporary access token** | WhatsApp → API Setup → Copiar | `EAAxxxx...` (largo) | Autenticación Bearer (caduca ~24h en prueba) |
| **Número de prueba de WhatsApp** | Misma pantalla (From) | `+1 555 123 4567` | Número al que escribiréis en la demo |

Tu compañero te los puede mandar por **WhatsApp privado** o gestor de contraseñas del equipo — nunca en el repo.

En tu `.env` local:

```env
WHATSAPP_ACCESS_TOKEN=EAA...
WHATSAPP_PHONE_NUMBER_ID=123456789012345
CHAT_CHANNEL=whatsapp
```

---

## 2. Acceso a tu celular en Meta (él lo configura, tú pruebas)

Tu compañero en **WhatsApp → API Setup → Para / To**:

- Añade **tu número** con código país (`57...`).
- Tú recibes un **código por WhatsApp** y se lo pasas para confirmar.

Sin esto **no** podrás chatear con el bot desde tu teléfono en la sustentación.

Opcional: añadir también el número del **profesor** como tester si Meta lo permite.

---

## 3. App en Meta Developers (para webhook N8N)

| Dato | Para qué |
|------|----------|
| **Nombre de la app** | Identificar en Meta (ej. `Riopaila Agente`) |
| **App ID** (opcional) | Documentación / soporte |
| **URL del webhook de N8N** (cuando esté activo) | La pegará en Meta → Configuration → Webhook |

El compañero (o tú) en Meta → **WhatsApp → Configuration**:

- **Callback URL:** URL de producción del nodo Webhook en N8N  
- **Verify token:** texto acordado (ej. `riopaila_n8n_2025`) — el mismo en N8N si aplica  
- Suscripción al campo **messages**

---

## 4. Roles en la app (recomendado)

En developers.facebook.com → tu app → **Roles** / **Funciones de la app**:

- Añadir tu cuenta Facebook como **Administrador** o **Desarrollador**.

Así puedes ver token, webhook y ejecutions en N8N sin depender solo de él el día de la demo.

---

## 5. Lo que TÚ montas (no se lo pides “copiado”, es tu PC)

| Pieza | Quién |
|-------|--------|
| Repo + `.env` con OpenAI y Supabase | Tú |
| `uvicorn` puerto 8000 | Tú |
| `ngrok http 8000` (si N8N está en la nube) | Tú |
| Workflow N8N importado + URL `/chat` | Tú |
| Token e Phone number ID en nodos N8N | Tú (los que te pasó el compañero) |

---

## 6. Mensaje listo para enviar al compañero

Copia y pega:

```
Hola, necesito esto para conectar WhatsApp al agente (Ruta A):

1) En developers.facebook.com → nuestra app → WhatsApp → API Setup:
   - Phone number ID (número largo, no es el teléfono +57)
   - Temporary access token (botón Copiar)

2) En "Para" / To: agregar mi celular 57XXXXXXXXXX para que me llegue el código de prueba.

3) El número de prueba de Meta (From) al que debemos escribir por WhatsApp.

4) Cuando tengamos N8N: pegar en WhatsApp → Configuration el webhook de N8N y suscribir "messages".

5) Añadirme como Desarrollador en la app (Roles).

NO subir token a GitHub. Me lo pasas por privado.
Gracias!
```

---

## 7. Día de la sustentación — quién hace qué

| Momento | Compañero | Tú |
|---------|-----------|-----|
| Antes | Renueva token si venció (API Setup) | API + ngrok + N8N activos |
| Demo | Opcional: pantalla Meta / N8N | Terminal uvicorn + celular con chat al número de prueba |
| Si falla token | Genera token nuevo y te lo pasa | Actualizas `.env` y nodo N8N |

---

## 8. Seguridad

- Token = contraseña. Solo `.env` local y gestor del equipo.
- Si el token se filtró: regenerar en Meta API Setup.
- El repo ya tiene `.env.example` sin secretos.
