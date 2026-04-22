"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { SessionDetail, SessionStatus } from "@/lib/types";

const POLL_INTERVAL = 3000;
const ACTIVE_STATUSES: SessionStatus[] = ["pending", "transcribing", "summarizing"];

export function useSessionStatus(sessionId: number) {
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);

  async function fetchSession() {
    try {
      const data = await apiFetch<SessionDetail>(`/sessions/${sessionId}`);
      setSession(data);
      return data;
    } catch (err) {
      console.error("Failed to fetch session:", err);
      return null;
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchSession();
  }, [sessionId]);

  useEffect(() => {
    if (!session) return;
    if (!ACTIVE_STATUSES.includes(session.status)) return;

    const interval = setInterval(fetchSession, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [session?.status, sessionId]);

  return { session, loading, refetch: fetchSession };
}
