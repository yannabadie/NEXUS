"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

// ============================================================================
// Types
// ============================================================================

export interface ChatMessage {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    timestamp: Date;
    isStreaming?: boolean;
}

interface ChatStoreContextValue {
    messages: ChatMessage[];
    addMessage: (message: ChatMessage) => void;
    clearMessages: () => void;
    isLoading: boolean;
    setIsLoading: (loading: boolean) => void;
}

// ============================================================================
// Context
// ============================================================================

const ChatStoreContext = createContext<ChatStoreContextValue | null>(null);

// ============================================================================
// Provider
// ============================================================================

export function ChatStoreProvider({ children }: { children: ReactNode }) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const addMessage = useCallback((message: ChatMessage) => {
        setMessages((prev) => [...prev, message]);
    }, []);

    const clearMessages = useCallback(() => {
        setMessages([]);
    }, []);

    return (
        <ChatStoreContext.Provider
            value={{
                messages,
                addMessage,
                clearMessages,
                isLoading,
                setIsLoading,
            }}
        >
            {children}
        </ChatStoreContext.Provider>
    );
}

// ============================================================================
// Hook
// ============================================================================

export function useChatStore() {
    const context = useContext(ChatStoreContext);
    if (!context) {
        throw new Error("useChatStore must be used within a ChatStoreProvider");
    }
    return context;
}
