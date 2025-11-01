"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createSession, finalizeSession } from "@/lib/api";

const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const wsBase = (process.env.NEXT_PUBLIC_WS_BASE ?? apiBase).replace("http", "ws");

const formatTimer = (ms: number) => {
  const total = Math.max(0, Math.floor(ms / 1000));
  const mm = String(Math.floor(total / 60)).padStart(2, "0");
  const ss = String(total % 60).padStart(2, "0");
  return `${mm}:${ss}`;
};

export function Recorder() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [timer, setTimer] = useState("00:00");
  const [status, setStatus] = useState("Bereit");
  const [summary, setSummary] = useState<any | null>(null);
  const [transcript, setTranscript] = useState<string | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const startRef = useRef<number>(0);

  const startTimer = () => {
    startRef.current = Date.now();
    timerRef.current && clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setTimer(formatTimer(Date.now() - startRef.current));
    }, 250);
  };

  const stopTimer = (reset = true) => {
    timerRef.current && clearInterval(timerRef.current);
    timerRef.current = null;
    if (reset) setTimer("00:00");
  };

  const cleanupAudio = useCallback(async () => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current.onaudioprocess = null;
      processorRef.current = null;
    }
    if (audioContextRef.current) {
      try {
        await audioContextRef.current.close();
      } catch (error) {
        console.warn("AudioContext close failed", error);
      }
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  const closeWebSocket = useCallback(async () => {
    const ws = wsRef.current;
    if (!ws) return;
    wsRef.current = null;
    ws.onopen = ws.onmessage = ws.onclose = ws.onerror = null;
    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
      ws.close(1000, "client-stop");
    }
  }, []);

  const handleAudioProcess = useCallback((event: AudioProcessingEvent) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const input = event.inputBuffer.getChannelData(0);
    const buffer = new ArrayBuffer(input.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < input.length; i += 1) {
      let sample = input[i];
      if (sample > 1) sample = 1;
      if (sample < -1) sample = -1;
      view.setInt16(i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    }
    ws.send(buffer);
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setSummary(null);
      setTranscript(null);
      setStatus("Sitzung wird vorbereitet …");
      const session = await createSession();
      setSessionId(session.id);
      const ws = new WebSocket(`${wsBase}${session.websocket_url}`);
      wsRef.current = ws;
      ws.binaryType = "arraybuffer";
      ws.onopen = () => setStatus("Mikrofon wird vorbereitet …");
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload?.bytes) {
            setStatus(`Aufnahme läuft … (${(payload.bytes / 1024).toFixed(1)} kB)`);
          }
        } catch {
          /* noop */
        }
      };
      ws.onerror = () => setStatus("WebSocket-Fehler");

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, sampleRate: 48000, echoCancellation: true },
      });
      streamRef.current = stream;
      const audioContext = new AudioContext({ sampleRate: 48000 });
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      processor.onaudioprocess = handleAudioProcess;
      const gain = audioContext.createGain();
      gain.gain.value = 0;
      source.connect(processor);
      processor.connect(gain);
      gain.connect(audioContext.destination);
      await audioContext.resume();
      startTimer();
      setStatus("Aufnahme läuft …");
    } catch (error) {
      console.error(error);
      setStatus("Start fehlgeschlagen");
      await cleanupAudio();
      await closeWebSocket();
      setSessionId(null);
      stopTimer();
    }
  }, [cleanupAudio, closeWebSocket, handleAudioProcess]);

  const stopRecording = useCallback(async () => {
    if (!sessionId) return;
    setStatus("Verarbeitung läuft …");
    stopTimer(false);
    await cleanupAudio();
    await closeWebSocket();
    try {
      const data = await finalizeSession(sessionId);
      setSummary(data.summary);
      setTranscript(data.transcript);
      setStatus("Bereit");
    } catch (error) {
      console.error(error);
      setStatus("Fehler bei der Verarbeitung");
    } finally {
      setSessionId(null);
      stopTimer();
    }
  }, [cleanupAudio, closeWebSocket, sessionId]);

  useEffect(() => {
    return () => {
      stopTimer();
      cleanupAudio();
      closeWebSocket();
    };
  }, [cleanupAudio, closeWebSocket]);

  const recording = Boolean(sessionId);

  return (
    <div className="space-y-4 rounded-xl border border-white/10 bg-slate-900/60 p-6 shadow-lg">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-semibold">Aufnahme</h2>
          <p className="text-sm text-slate-300">Status: {status}</p>
        </div>
        <div className="flex items-center gap-3 text-lg font-mono">
          <span className={`h-3 w-3 rounded-full ${recording ? "bg-red-500 animate-pulse" : "bg-slate-500"}`} />
          <span>{timer}</span>
        </div>
      </div>
      <div className="flex flex-wrap gap-3">
        {!recording && (
          <button
            className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 shadow hover:bg-emerald-400"
            onClick={startRecording}
          >
            Aufnahme starten
          </button>
        )}
        {recording && (
          <button
            className="rounded-md bg-rose-500 px-4 py-2 text-sm font-semibold text-rose-50 shadow hover:bg-rose-400"
            onClick={stopRecording}
          >
            Aufnahme stoppen
          </button>
        )}
      </div>
      {transcript && (
        <div className="rounded-md border border-white/10 bg-black/30 p-4">
          <h3 className="text-lg font-semibold">Transkript</h3>
          <p className="mt-2 whitespace-pre-wrap text-sm text-slate-200">{transcript}</p>
        </div>
      )}
      {summary && (
        <div className="rounded-md border border-white/10 bg-black/30 p-4">
          <h3 className="text-lg font-semibold">Protokoll</h3>
          {"sections" in summary && summary.sections ? (
            <div className="mt-3 space-y-3">
              {Object.entries(summary.sections as Record<string, string>).map(([sectionName, sectionText]) => (
                <div key={sectionName}>
                  <p className="text-sm font-semibold text-slate-100">{sectionName}</p>
                  <p className="mt-1 text-sm text-slate-200">{sectionText || "Keine Inhalte vorhanden."}</p>
                </div>
              ))}
            </div>
          ) : (
            <pre className="mt-2 whitespace-pre-wrap text-sm text-slate-200">{JSON.stringify(summary, null, 2)}</pre>
          )}
          {"highlights" in summary && Array.isArray(summary.highlights) && summary.highlights.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-semibold text-slate-100">Highlights</p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-200">
                {summary.highlights.map((item: string, index: number) => (
                  <li key={`${item}-${index}`}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

