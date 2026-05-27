"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, type CurrentUser, type Note } from "@/lib/api";

export default function DashboardPage() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [me, list] = await Promise.all([
        apiFetch<CurrentUser>("/auth/me"),
        apiFetch<Note[]>("/notes"),
      ]);
      setUser(me);
      setNotes(list);
    } catch {
      setError("Please sign in to view your dashboard.");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function addNote(e: React.FormEvent) {
    e.preventDefault();
    await apiFetch<Note>("/notes", {
      method: "POST",
      body: JSON.stringify({ title, body }),
    });
    setTitle("");
    setBody("");
    await load();
  }

  if (error) {
    return (
      <main className="section">
        <p className="error">{error}</p>
        <Link href="/signin" className="btn btn-primary">
          Sign in
        </Link>
      </main>
    );
  }

  return (
    <main className="section">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2 style={{ margin: 0 }}>Dashboard</h2>
        {user && (
          <span
            className={`badge ${
              user.subscription_status === "active" ? "badge-active" : "badge-inactive"
            }`}
          >
            {user.subscription_status}
          </span>
        )}
      </div>
      <p className="muted">Organization #{user?.tenant_id}</p>

      <form className="card" onSubmit={addNote} style={{ marginBottom: 24 }}>
        <div className="field">
          <label htmlFor="title">Note title</label>
          <input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="body">Body</label>
          <input id="body" value={body} onChange={(e) => setBody(e.target.value)} />
        </div>
        <button className="btn btn-primary" type="submit">
          Add note
        </button>
      </form>

      {notes.map((note) => (
        <div key={note.id} className="note">
          <p className="note-title">{note.title}</p>
          <p className="muted">{note.body}</p>
          {note.summary && <p className="note-summary">Summary: {note.summary}</p>}
        </div>
      ))}

      <Link href="/feature" className="btn">
        Open the feature
      </Link>
    </main>
  );
}
