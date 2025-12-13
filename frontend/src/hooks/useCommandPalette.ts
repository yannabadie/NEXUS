"use client";

import { useState, useEffect, useCallback } from "react";

/**
 * Hook for managing Command Palette state and keyboard shortcuts.
 */
export function useCommandPalette() {
    const [isOpen, setIsOpen] = useState(false);

    const open = useCallback(() => setIsOpen(true), []);
    const close = useCallback(() => setIsOpen(false), []);
    const toggle = useCallback(() => setIsOpen((prev) => !prev), []);

    // Global keyboard shortcut: Ctrl+K / Cmd+K
    useEffect(() => {
        function handleKeyDown(event: KeyboardEvent) {
            // Ctrl+K or Cmd+K
            if ((event.ctrlKey || event.metaKey) && event.key === "k") {
                event.preventDefault();
                toggle();
            }

            // Escape to close
            if (event.key === "Escape" && isOpen) {
                event.preventDefault();
                close();
            }
        }

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isOpen, toggle, close]);

    return {
        isOpen,
        open,
        close,
        toggle,
    };
}

export default useCommandPalette;
