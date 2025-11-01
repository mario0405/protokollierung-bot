import { create } from "zustand";

export type TemplateSettings = {
  language: string;
  tone: string;
  sections: string[];
  meeting_type?: string | null;
  audience?: string | null;
  objectives?: string | null;
  notes?: string | null;
};

type SettingsState = {
  settings: TemplateSettings;
  loading: boolean;
  setSettings: (settings: TemplateSettings) => void;
  setLoading: (value: boolean) => void;
};

const defaultSettings: TemplateSettings = {
  language: "de",
  tone: "praegnant",
  sections: [
    "Agenda-Ueberblick",
    "Entscheidungen",
    "Aufgaben",
    "Verantwortliche",
    "Fristen",
    "Risiken",
    "Offene Punkte",
  ],
  meeting_type: "",
  audience: "",
  objectives: "",
  notes: "",
};

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: defaultSettings,
  loading: false,
  setSettings: (settings) => set({ settings }),
  setLoading: (loading) => set({ loading }),
}));
