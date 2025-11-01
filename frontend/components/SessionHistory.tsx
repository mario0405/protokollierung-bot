"use client";

import useSWR from "swr";
import { listSessions, Session } from "@/lib/api";

const fetcher = async () => listSessions();

export function SessionHistory() {
  const { data, error, isLoading, mutate } = useSWR("sessions", fetcher, { refreshInterval: 10000 });

  return (
    <div className="space-y-4 rounded-xl border border-white/10 bg-slate-900/60 p-6 shadow-lg">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Verlauf</h2>
          <p className="text-sm text-slate-300">Zuletzt aufgezeichnete Sitzungen</p>
        </div>
        <button
          onClick={() => mutate()}
          className="rounded-md bg-white/10 px-3 py-2 text-sm text-slate-200 hover:bg-white/20"
        >
          Aktualisieren
        </button>
      </div>
      {isLoading && <p className="text-sm text-slate-300">Lade...</p>}
      {error && <p className="text-sm text-rose-400">Fehler beim Laden</p>}
      <div className="space-y-3">
        {data?.map((session: Session) => (
          <div key={session.id} className="rounded-md border border-white/10 bg-black/30 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-slate-100">
                  {session.title?.trim() ||
                    (session.created_at ? `Sitzung vom ${new Date(session.created_at).toLocaleDateString()}` : "Unbenannte Sitzung")}
                </p>
                <p className="font-mono text-xs text-slate-400">{session.id}</p>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold ${
                  session.status === "completed" ? "bg-emerald-500/80 text-emerald-950" : "bg-amber-500/80 text-amber-950"
                }`}
              >
                {session.status}
              </span>
            </div>
            <div className="mt-2 text-xs text-slate-400">
              <p>Gestartet: {session.created_at ? new Date(session.created_at).toLocaleString() : "-"}</p>
              <p>Aktualisiert: {session.updated_at ? new Date(session.updated_at).toLocaleString() : "-"}</p>
              <p>Transkript: {session.has_transcript ? "ja" : "nein"}</p>
            </div>
          </div>
        ))}
        {data && data.length === 0 && <p className="text-sm text-slate-400">Noch keine Sitzungen vorhanden.</p>}
      </div>
    </div>
  );
}

