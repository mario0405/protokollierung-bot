"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchSettings, updateSettings } from "@/lib/api";
import { useSettingsStore } from "@/lib/stores/settingsStore";

const BASE_SECTION_OPTIONS = [
  "Agenda-Ueberblick",
  "Entscheidungen",
  "Aufgaben",
  "Verantwortliche",
  "Fristen",
  "Risiken",
  "Offene Punkte",
  "Lessons Learned",
];

export function SettingsForm() {
  const { settings, setSettings, loading, setLoading } = useSettingsStore();
  const [message, setMessage] = useState<string | null>(null);
  const [newSection, setNewSection] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const result = await fetchSettings();
        setSettings(result.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [setLoading, setSettings]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    try {
      const formData = new FormData(event.currentTarget);
      const payload = {
        data: {
          language: formData.get("language")?.toString() ?? "de",
          tone: formData.get("tone")?.toString() ?? "praegnant",
          meeting_type: formData.get("meeting_type")?.toString() ?? "",
          audience: formData.get("audience")?.toString() ?? "",
          objectives: formData.get("objectives")?.toString() ?? "",
          notes: formData.get("notes")?.toString() ?? "",
          sections: settings.sections,
        },
      };
      const result = await updateSettings(payload.data);
      setSettings(result.data);
      setMessage("Einstellungen gespeichert");
    } catch (error) {
      console.error(error);
      setMessage("Fehler beim Speichern");
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    const has = settings.sections.includes(section);
    const updated = has ? settings.sections.filter((s) => s !== section) : [...settings.sections, section];
    setSettings({ ...settings, sections: updated });
  };

  const handleAddSection = () => {
    const label = newSection.trim();
    if (!label) return;
    if (!settings.sections.includes(label)) {
      setSettings({ ...settings, sections: [...settings.sections, label] });
    }
    setNewSection("");
  };

  const availableSections = useMemo(() => {
    return Array.from(new Set([...BASE_SECTION_OPTIONS, ...settings.sections]));
  }, [settings.sections]);

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-white/10 bg-slate-900/60 p-6 shadow-lg">
      <div>
        <h2 className="text-xl font-semibold">Einstellungen</h2>
        <p className="text-sm text-slate-300">Steuere deine Protokoll-Vorlage.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-medium text-slate-200">
          Sprache
          <select
            name="language"
            defaultValue={settings.language}
            key={settings.language}
            className="mt-1 w-full rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring"
          >
            <option value="de">Deutsch</option>
            <option value="en">Englisch</option>
          </select>
        </label>
        <label className="text-sm font-medium text-slate-200">
          Tonfall
          <input
            name="tone"
            defaultValue={settings.tone}
            className="mt-1 w-full rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring"
          />
        </label>
        <label className="text-sm font-medium text-slate-200">
          Besprechungstyp
          <input
            name="meeting_type"
            defaultValue={settings.meeting_type ?? ""}
            className="mt-1 w-full rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring"
          />
        </label>
        <label className="text-sm font-medium text-slate-200">
          Zielgruppe
          <input
            name="audience"
            defaultValue={settings.audience ?? ""}
            className="mt-1 w-full rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring"
          />
        </label>
      </div>
      <label className="text-sm font-medium text-slate-200">
        Ziele
        <textarea
          name="objectives"
          defaultValue={settings.objectives ?? ""}
          className="mt-1 h-24 w-full rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring"
        />
      </label>
      <label className="text-sm font-medium text-slate-200">
        Zusaetzliche Notizen
        <textarea
          name="notes"
          defaultValue={settings.notes ?? ""}
          className="mt-1 h-24 w-full rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring"
        />
      </label>
      <div>
        <p className="text-sm font-medium text-slate-200">Abschnitte</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {availableSections.map((section) => {
            const active = settings.sections.includes(section);
            return (
              <button
                key={section}
                type="button"
                onClick={() => toggleSection(section)}
                className={`rounded-full px-3 py-1 text-xs font-semibold ${
                  active ? "bg-emerald-500 text-emerald-950" : "bg-black/40 text-slate-300"
                }`}
              >
                {section}
              </button>
            );
          })}
        </div>
        <div className="mt-3 flex gap-2">
          <input
            type="text"
            value={newSection}
            onChange={(event) => setNewSection(event.target.value)}
            placeholder="Eigenen Abschnitt eingeben"
            className="flex-1 rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring"
          />
          <button
            type="button"
            onClick={handleAddSection}
            className="rounded-md bg-emerald-500 px-3 py-2 text-sm font-semibold text-emerald-950 hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-emerald-600/40"
            disabled={!newSection.trim()}
          >
            Hinzufuegen
          </button>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          type="submit"
          className="rounded-md bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-sky-600/40"
          disabled={loading}
        >
          Speichern
        </button>
        {message && <span className="text-sm text-slate-300">{message}</span>}
      </div>
    </form>
  );
}
