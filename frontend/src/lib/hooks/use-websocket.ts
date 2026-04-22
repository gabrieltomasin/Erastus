"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { SessionDetail, SessionStatus, ProcessingLog } from "@/lib/types";

const WS_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const WS_URL = WS_BASE
  ? WS_BASE.replace(/^http/, "ws") + "/api"
  : `${typeof window !== "undefined" ? window.location.protocol.replace(/^http/, "ws") : "ws:"}//${typeof window !== "undefined" ? window.location.host : "localhost:3000"}/api`;
const POLL_INTERVAL = 5000;
const ACTIVE_STATUSES: SessionStatus[] = ["pending", "transcribing", "summarizing"];

export interface WSEvent {
  type: "status_change" | "log" | "progress" | "connected";
  status?: SessionStatus;
  step?: string;
  message?: string;
  level?: string;
  current?: number;
  total?: number;
  percent?: number;
  detail?: string;
}

export function useSessionUpdates(sessionId: number) {
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [liveLogs, setLiveLogs] = useState<ProcessingLog[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchSession = useCallback(async () => {
    try {
      const data = await apiFetch<SessionDetail>(`/sessions/${sessionId}`);
      setSession(data);
      setLiveLogs(data.processing_logs || []);
      return data;
    } catch (err) {
      console.error("Failed to fetch session:", err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const startPolling = useCallback(() => {
    if (pollingRef.current) return;
    pollingRef.current = setInterval(fetchSession, POLL_INTERVAL);
  }, [fetchSession]);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  useEffect(() => {
    if (!session) return;
    if (!ACTIVE_STATUSES.includes(session.status)) return;

    // Try WebSocket
    const ws = new WebSocket(`${WS_URL}/ws/sessions/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      stopPolling();
    };

    ws.onmessage = (event) => {
      try {
        const evt: WSEvent = JSON.parse(event.data);
        if (evt.type === "status_change" && evt.status) {
          setSession((prev) => prev ? { ...prev, status: evt.status! } : prev);
        }
        if (evt.type === "log") {
          const log: ProcessingLog = {
            id: Date.now(),
            session_id: sessionId,
            step: evt.step || "unknown",
            message: evt.message || "",
            level: evt.level || "info",
            timestamp: new Date().toISOString(),
          };
          setLiveLogs((prev) => [...prev, log]);
        }
      } catch {}
    };

    ws.onerror = () => {
      setIsConnected(false);
      startPolling();
    };

    ws.onclose = () => {
      setIsConnected(false);
      startPolling();
    };

    // Also start polling as backup until WS connects
    const connectTimeout = setTimeout(() => {
      if (!isConnected) startPolling();
    }, 3000);

    return () => {
      clearTimeout(connectTimeout);
      ws.close();
      wsRef.current = null;
      stopPolling();
    };
  }, [session?.status, sessionId]);

  return { session, loading, refetch: fetchSession, liveLogs, isConnected };
}
