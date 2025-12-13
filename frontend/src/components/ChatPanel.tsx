"use client";

import { useState, useRef, useEffect, useCallback, FormEvent } from "react";
import { sendChatMessage } from "@/lib/api";

// ============================================================================
// Types
// ============================================================================

interface Message {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    timestamp: Date;
    isStreaming?: boolean;
}

interface ChatPanelProps {
    className?: string;
    onNewMessage?: (message: Message) => void;
}

// ============================================================================
// Chat Panel Component
// ============================================================================

export function ChatPanel({ className = "", onNewMessage }: ChatPanelProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Auto-scroll to bottom on new messages
    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);

    // Handle form submission
    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: `user-${Date.now()}`,
            role: "user",
            content: input.trim(),
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);
        onNewMessage?.(userMessage);

        try {
            // Send to backend
            const result = await sendChatMessage(input.trim());

            if (result.data?.response) {
                const assistantMessage: Message = {
                    id: `assistant-${Date.now()}`,
                    role: "assistant",
                    content: result.data.response,
                    timestamp: new Date(),
                };
                setMessages((prev) => [...prev, assistantMessage]);
                onNewMessage?.(assistantMessage);
            } else if (result.error) {
                const errorMessage: Message = {
                    id: `error-${Date.now()}`,
                    role: "system",
                    content: `Error: ${result.error}`,
                    timestamp: new Date(),
                };
                setMessages((prev) => [...prev, errorMessage]);
            }
        } catch (error) {
            const errorMessage: Message = {
                id: `error-${Date.now()}`,
                role: "system",
                content: `Connection error: ${error instanceof Error ? error.message : "Unknown error"}`,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
            inputRef.current?.focus();
        }
    };

    // Handle quick commands
    const quickCommands = [
        { label: "/help", cmd: "/help" },
        { label: "/status", cmd: "/status" },
        { label: "/evolve", cmd: "/evolve" },
    ];

    return (
        <div className={`flex flex-col bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden ${className}`}>
            {/* Header */}
            <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-lg">💬</span>
                    <span className="font-medium text-zinc-200">NEXUS Chat</span>
                </div>
                <div className={`flex items-center gap-2 text-xs ${isLoading ? "text-amber-400" : "text-zinc-500"}`}>
                    {isLoading ? (
                        <>
                            <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
                            Processing...
                        </>
                    ) : (
                        <>
                            <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                            Ready
                        </>
                    )}
                </div>
            </div>

            {/* Messages Container */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[200px] max-h-[400px]">
                {messages.length === 0 && (
                    <div className="text-center text-zinc-500 py-8">
                        <div className="text-3xl mb-2">🤖</div>
                        <div className="text-sm">Start a conversation with NEXUS</div>
                        <div className="text-xs mt-1">Try: "Hello" or use commands like /help</div>
                    </div>
                )}

                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                        <div
                            className={`max-w-[80%] rounded-xl px-4 py-2 ${message.role === "user"
                                    ? "bg-violet-600 text-white"
                                    : message.role === "system"
                                        ? "bg-red-900/30 border border-red-700 text-red-200"
                                        : "bg-zinc-800 text-zinc-200"
                                }`}
                        >
                            {/* Role indicator for assistant */}
                            {message.role === "assistant" && (
                                <div className="text-xs text-zinc-400 mb-1 flex items-center gap-1">
                                    <span>🧠</span> NEXUS
                                </div>
                            )}

                            {/* Content */}
                            <div className="text-sm whitespace-pre-wrap break-words">
                                {message.content}
                                {message.isStreaming && (
                                    <span className="inline-block w-2 h-4 bg-current animate-pulse ml-1" />
                                )}
                            </div>

                            {/* Timestamp */}
                            <div className={`text-xs mt-1 ${message.role === "user" ? "text-violet-300" : "text-zinc-500"
                                }`}>
                                {message.timestamp.toLocaleTimeString()}
                            </div>
                        </div>
                    </div>
                ))}

                {/* Loading indicator */}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-zinc-800 rounded-xl px-4 py-3">
                            <div className="flex gap-1">
                                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Quick Commands */}
            <div className="px-4 py-2 border-t border-zinc-800/50 flex gap-2">
                {quickCommands.map((cmd) => (
                    <button
                        key={cmd.cmd}
                        onClick={() => setInput(cmd.cmd)}
                        className="px-2 py-1 text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200 rounded transition-colors"
                    >
                        {cmd.label}
                    </button>
                ))}
            </div>

            {/* Input Form */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-zinc-800">
                <div className="flex gap-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Message NEXUS..."
                        disabled={isLoading}
                        className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent disabled:opacity-50"
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
                    >
                        Send
                    </button>
                </div>
            </form>
        </div>
    );
}

export default ChatPanel;
