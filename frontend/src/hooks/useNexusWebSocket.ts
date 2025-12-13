"use client";

import { useEffect, useRef, useState, useCallback } from "react";

interface NexusMessage {
    type: string;
    data: unknown;
    timestamp: string;
}

interface UseNexusWebSocketOptions {
    onMessage?: (message: NexusMessage) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    autoReconnect?: boolean;
    reconnectInterval?: number;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export function useNexusWebSocket(options: UseNexusWebSocketOptions = {}) {
    const {
        onMessage,
        onConnect,
        onDisconnect,
        autoReconnect = true,
        reconnectInterval = 3000,
    } = options;

    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState<NexusMessage | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        try {
            wsRef.current = new WebSocket(WS_URL);

            wsRef.current.onopen = () => {
                console.log("[NEXUS WS] Connected to", WS_URL);
                setIsConnected(true);
                onConnect?.();
            };

            wsRef.current.onmessage = (event) => {
                try {
                    const message: NexusMessage = JSON.parse(event.data);
                    setLastMessage(message);
                    onMessage?.(message);
                } catch (e) {
                    console.warn("[NEXUS WS] Failed to parse message:", e);
                }
            };

            wsRef.current.onclose = () => {
                console.log("[NEXUS WS] Disconnected");
                setIsConnected(false);
                onDisconnect?.();

                if (autoReconnect) {
                    reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
                }
            };

            wsRef.current.onerror = (error) => {
                console.error("[NEXUS WS] Error:", error);
            };
        } catch (error) {
            console.error("[NEXUS WS] Connection failed:", error);
        }
    }, [onMessage, onConnect, onDisconnect, autoReconnect, reconnectInterval]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        wsRef.current?.close();
    }, []);

    const send = useCallback((data: unknown) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        } else {
            console.warn("[NEXUS WS] Cannot send - not connected");
        }
    }, []);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        isConnected,
        lastMessage,
        send,
        connect,
        disconnect,
    };
}
