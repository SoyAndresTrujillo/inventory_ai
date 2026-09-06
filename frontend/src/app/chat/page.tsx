"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

// ponytail: dictation uses the browser's built-in Web Speech API (Chrome/Edge).
// Swap for a transcription endpoint if Firefox/Safari support is needed.
type Recognition = {
  lang: string;
  interimResults: boolean;
  start(): void;
  stop(): void;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onend: (() => void) | null;
};

function createRecognition(): Recognition | null {
  const w = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [provider, setProvider] = useState("");
  const [error, setError] = useState("");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<Recognition | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  function dictate() {
    if (listening) {
      recognitionRef.current?.stop();
      return;
    }
    const recognition = createRecognition();
    if (!recognition) {
      setError("Voice input needs Chrome or Edge. Type or attach a file instead.");
      return;
    }
    recognition.lang = navigator.language;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = Array.from({ length: event.results.length }, (_, i) => event.results[i][0].transcript).join(" ");
      setInput((current) => (current ? `${current} ${transcript}` : transcript));
    };
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }

  async function send(event: React.FormEvent) {
    event.preventDefault();
    if (!input.trim() && files.length === 0) return;
    setError("");

    const shown = [input.trim(), ...files.map((f) => `📎 ${f.name}`)].filter(Boolean).join("\n");
    const history = messages;
    setMessages([...history, { role: "user", content: shown }]);
    const sentInput = input;
    const sentFiles = files;
    setInput("");
    setFiles([]);
    setBusy(true);

    try {
      const { reply, provider: usedProvider } = await api.chat(sentInput, history, sentFiles);
      setProvider(usedProvider);
      setMessages((current) => [...current, { role: "assistant", content: reply }]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-9rem)] flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">AI assistant</h1>
        <p className="mt-1 text-sm text-muted">
          Create, update or delete products by chat. Attach Excel, CSV, XML, JSON — photos and PDF
          on vision-capable providers.
          {provider && (
            <span className="ml-2 rounded-full border border-line px-2 py-0.5 text-xs">
              {provider}
            </span>
          )}
        </p>
      </div>

      <div className="card flex-1 space-y-4 overflow-y-auto">
        {messages.length === 0 && (
          <p className="py-10 text-center text-sm text-muted">
            Try: “Add 3 Bosch drills, SKU DR-1 to DR-3, 89.90 each, 10 in stock, made in Colombia.”
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={message.role === "user" ? "flex justify-end" : "flex justify-start"}
          >
            <div
              className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm ${
                message.role === "user"
                  ? "bg-accent text-white"
                  : "border border-line bg-background"
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        {busy && <p className="text-sm text-muted">Working…</p>}
        <div ref={bottomRef} />
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <form onSubmit={send} className="card space-y-3">
        {files.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {files.map((file) => (
              <span
                key={file.name}
                className="rounded-full border border-line px-3 py-1 text-xs text-muted"
              >
                {file.name}
              </span>
            ))}
          </div>
        )}
        <div className="flex items-end gap-2">
          <textarea
            className="input min-h-11 resize-none"
            rows={1}
            placeholder="Describe what to create, update or delete…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(e);
              }
            }}
          />
          <label className="btn-ghost cursor-pointer whitespace-nowrap">
            Attach
            <input
              type="file"
              multiple
              hidden
              accept="image/*,.csv,.json,.xml,.xlsx,.xlsm,.txt,.pdf"
              onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            />
          </label>
          <button
            type="button"
            onClick={dictate}
            className={`btn-ghost whitespace-nowrap ${listening ? "text-accent" : ""}`}
          >
            {listening ? "Stop" : "Voice"}
          </button>
          <button className="btn" disabled={busy}>
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
