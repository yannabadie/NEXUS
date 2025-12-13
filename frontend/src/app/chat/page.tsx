"use client";

import { ChatPanel } from "@/components/ChatPanel";
import { AgentExchanges } from "@/components/AgentExchanges";

export default function ChatPage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Chat</h1>
                    <p className="text-sm text-zinc-400">Interact with NEXUS agents</p>
                </div>
            </div>

            {/* Chat Panel - Full Width */}
            <ChatPanel className="min-h-[400px]" />

            {/* Agent Exchanges - Live Feed */}
            <AgentExchanges className="min-h-[300px]" />
        </div>
    );
}
