"use client";

import { useEffect, useState } from "react";
import { apiFetch, type Note } from "@/lib/api";

export default function FeaturePage() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function load() {
    try {
      setNotes(await apiFetch<Note[]>("/notes"));
    } catch {
      setError("Please sign in to use this feature.");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function summarize(id: number) {
    setBusyId(id);
    try {
      await apiFetch<{ id: number; summary: string }>(`/notes/${id}/summarize`, {
        method: "POST",
      });
      await load();
    } finally {
      setBusyId(null);
    }
  }

  if (error) {
    return (
      <main className="section">
        <p className="error">{error}</p>
      </main>
    );
  }

  return (
    <main className="section">
      <h2>Summarize</h2>
      <p className="muted">
        Generate a short summary of any note through the provider seam. Swap the provider to
        connect your own backend.
      </p>
      {notes.map((note) => (
        <div key={note.id} className="note">
          <p className="note-title">{note.title}</p>
          <p className="muted">{note.body}</p>
          {note.summary && <p className="note-summary">Summary: {note.summary}</p>}
          <div style={{ marginTop: 10 }}>
            <button
              className="btn"
              onClick={() => summarize(note.id)}
              disabled={busyId === note.id}
            >
              {busyId === note.id ? "Working..." : "Summarize"}
            </button>
          </div>
        </div>
      ))}
    </main>
  );
}
