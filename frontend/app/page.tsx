import { Recorder } from "@/components/Recorder";
import { SessionHistory } from "@/components/SessionHistory";
import { SettingsForm } from "@/components/SettingsForm";

export default function Page() {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-8">
      <header className="space-y-2">
        <span className="rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-wide text-slate-300">
          Protocolito – Intelligente Protokolle. Klar. Schnell. Strukturiert.
        </span>
        <h1 className="text-4xl font-bold">Protocolito – Intelligente Protokolle. Klar. Schnell. Strukturiert.</h1>
        <p className="max-w-2xl text-slate-300">
          Zeichne Audio direkt im Browser auf, transkribiere mit Whisper und lasse das Protokoll durch Ollama erzeugen.
        </p>
      </header>
      <div className="grid gap-8 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-8">
          <Recorder />
          <SessionHistory />
        </div>
        <div>
          <SettingsForm />
        </div>
      </div>
    </main>
  );
}

