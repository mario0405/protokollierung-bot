Protocolito - Headless Meeting Recorder & Protokoll-Assistent
=============================================================

Mit dieser Stack-Kombination kannst du Meetings live im Browser aufzeichnen, automatisch transkribieren (Whisper) und über Ollama strukturierte Protokolle erzeugen. Das Setup besteht aus

- Frontend: Next.js 14 (React + TypeScript + TailwindCSS) mit Zustand für State, WebSocket-Streaming via MediaRecorder
- Backend: FastAPI + PostgreSQL + SQLAlchemy, Echtzeit-WebSocket für Audio, Whisper (faster-whisper) zur Transkription, Ollama (Llama 3 standardmäßig) für Zusammenfassungen
- Infrastruktur: Docker Compose mit Services `web`, `api`, `db`, `ollama`

---
Schnellstart mit Docker/Desktop
------------------------------
1. Konfiguriere optional `.env` (Ausgangspunkt `.env.example`). Standardmäßig nutzt der Ollama-Container den Host-Port **11535**. Falls auf deinem Rechner bereits ein Dienst auf 11434 läuft, musst du nichts weiter tun; soll ein anderer Port genutzt werden, setze `OLLAMA_HOST_PORT=<freier Port>`.
2. `docker compose up --build`
3. Frontend: http://localhost:3000
4. API: http://localhost:8000 (Healthcheck `/api/health` ? `{ "status": "bereit" }`)
5. PostgreSQL läuft auf Port 5432 (Standardzugang aus Compose-Datei)

Beim ersten Start lädt Ollama das gewünschte Modell; das kann einige Minuten dauern. Whisper-Modelle werden ebenfalls beim ersten Transkriptionslauf in den Container-Cache gelegt.

Lokale Entwicklung (ohne Docker)
--------------------------------
*Backend*
```
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Setze in diesem Fall `DATABASE_URL` in `.env` auf eine lokale Postgres-Instanz oder nutze SQLite (`sqlite:///./protocolito.db`). Für Ollama verbindest du dich entweder mit einem lokalen Server (`OLLAMA_HOST=http://localhost:11434`) oder entfernst entsprechende Features.

*Frontend*
```
cd frontend
npm install
npm run dev
```
Passe `.env.local` im Frontend an (z.?B. `NEXT_PUBLIC_API_BASE=http://localhost:8000`).

Wichtige Endpunkte (Backend)
----------------------------
- `POST /api/sessions` – neue Aufnahme starten, liefert Session-ID + WebSocket-URL
- `WEBSOCKET /ws/sessions/{id}` – Roh-Audio als 16-bit PCM streamen
- `POST /api/sessions/{id}/finalize` – Transkription + Protokoll generieren
- `GET /api/sessions` – Sitzungsverlauf
- `GET /api/sessions/{id}/transcript` – Transkript + Summary abrufen
- `GET/PUT /api/settings` – Protokollvorlage & Metadaten speichern

Projektstruktur
---------------
- `backend/app/` – FastAPI-Anwendung (Router, Services, Modelle)
- `frontend/app/` – Next.js App Router Pages
- `docker-compose.yml` – orchestriert Datenbank, API, Web, Ollama
- `storage/` (Volume) – persistente Audiodateien & Modellartefakte

Tipps
-----
- `OLLAMA_HOST_PORT` steuert lediglich das Host-Mapping; innerhalb des Compose-Netzwerks bleibt der Service unter `http://ollama:11434` erreichbar. Nutze einen anderen Wert, falls 11535 auf deinem Rechner blockiert ist.
- Wenn du bereits eine Ollama-Instanz betreibst, kannst du den Compose-Service `ollama` überspringen und `OLLAMA_HOST` auf deine bestehende URL setzen.
- Für Live-Transkription via WebSocket müssen Browser-Medienberechtigungen erteilt sein; das Frontend zeigt Timer, Status und streamt PCM-Chunks.
- Nach erfolgreichen Aufnahmen werden Audio (Datei + BLOB), Transkript und Summary in PostgreSQL gespeichert; der Storage-Ordner dient als Backup.

Viel Erfolg beim Automatisieren deiner Meeting-Protokolle!
