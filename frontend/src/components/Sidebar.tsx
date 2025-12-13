"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { NAV_ITEMS } from "@/lib/design-tokens";

// ============================================================================
// Types
// ============================================================================

interface SidebarProps {
    className?: string;
    onOpenCommandPalette?: () => void;
}

// ============================================================================
// Sidebar Component
// ============================================================================

export function Sidebar({ className = "", onOpenCommandPalette }: SidebarProps) {
    const pathname = usePathname();
    const [isCollapsed, setIsCollapsed] = useState(false);

    return (
        <aside
            className={`
        flex flex-col bg-zinc-900/50 border-r border-zinc-800
        transition-all duration-300
        ${isCollapsed ? "w-16" : "w-56"}
        ${className}
      `}
        >
            {/* Logo Section */}
            <div className="flex items-center gap-3 p-4 border-b border-zinc-800">
                <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-bold text-sm">N</span>
                </div>
                {!isCollapsed && (
                    <div className="overflow-hidden">
                        <h1 className="text-lg font-semibold text-white leading-tight">NEXUS</h1>
                        <p className="text-xs text-zinc-400 truncate">Collaborative Intelligence</p>
                    </div>
                )}
            </div>

            {/* Command Palette Trigger */}
            <button
                onClick={onOpenCommandPalette}
                className={`
          mx-2 mt-4 flex items-center gap-2 p-2 rounded-lg
          bg-zinc-800/50 border border-zinc-700 hover:border-zinc-600
          text-zinc-400 hover:text-zinc-200 transition-all
          ${isCollapsed ? "justify-center" : ""}
        `}
                title="Command Palette (Ctrl+K)"
            >
                <span>🔍</span>
                {!isCollapsed && (
                    <>
                        <span className="text-sm flex-1 text-left">Search...</span>
                        <kbd className="text-xs bg-zinc-700 px-1.5 py-0.5 rounded">⌘K</kbd>
                    </>
                )}
            </button>

            {/* Navigation Items */}
            <nav className="flex-1 mt-4 px-2 space-y-1">
                {NAV_ITEMS.map((item) => {
                    const isActive = pathname === item.href ||
                        (item.href !== "/" && pathname.startsWith(item.href));

                    return (
                        <Link
                            key={item.id}
                            href={item.href}
                            className={`
                flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all
                ${isActive
                                    ? "bg-violet-600/20 text-violet-300 border border-violet-600/50"
                                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
                                }
                ${isCollapsed ? "justify-center" : ""}
              `}
                            title={isCollapsed ? item.label : undefined}
                        >
                            <span className="text-lg">{item.icon}</span>
                            {!isCollapsed && (
                                <span className="text-sm font-medium">{item.label}</span>
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Bottom Section */}
            <div className="p-2 border-t border-zinc-800">
                {/* Collapse Toggle */}
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="w-full flex items-center justify-center gap-2 p-2 rounded-lg
                     text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 transition-all"
                    title={isCollapsed ? "Expand" : "Collapse"}
                >
                    <span className="text-lg">
                        {isCollapsed ? "»" : "«"}
                    </span>
                    {!isCollapsed && (
                        <span className="text-sm">Collapse</span>
                    )}
                </button>
            </div>
        </aside>
    );
}

export default Sidebar;
