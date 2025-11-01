import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Protocolito",
  description: "Erstelle Meeting-Protokolle mit Whisper und Ollama",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className="min-h-screen bg-slate-950 text-slate-50">
        {children}
      </body>
    </html>
  );
}

