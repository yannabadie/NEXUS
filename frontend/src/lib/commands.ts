/**
 * NEXUS Command Registry
 * 
 * All available commands for the Command Palette.
 * Organized by category with keyboard shortcuts where applicable.
 */

export interface Command {
    id: string;
    label: string;
    category: 'collaboration' | 'evolution' | 'monitoring' | 'workspace' | 'system' | 'navigation';
    shortcut?: string;
    icon: string;
    description: string;
    action: string; // Either a route or a command to execute
    actionType: 'navigate' | 'command' | 'api';
}

// ============================================================================
// Navigation Commands
// ============================================================================

const NAVIGATION_COMMANDS: Command[] = [
    { id: 'nav-dashboard', label: 'Dashboard', category: 'navigation', icon: '📊', description: 'Go to main dashboard', action: '/', actionType: 'navigate' },
    { id: 'nav-chat', label: 'Chat', category: 'navigation', icon: '💬', description: 'Open chat interface', action: '/chat', actionType: 'navigate' },
    { id: 'nav-hivemind', label: 'HiveMind', category: 'navigation', icon: '🐝', description: 'View HiveMind pipeline', action: '/hivemind', actionType: 'navigate' },
    { id: 'nav-agents', label: 'Agents', category: 'navigation', icon: '🤖', description: 'Manage agents', action: '/agents', actionType: 'navigate' },
    { id: 'nav-analytics', label: 'Analytics', category: 'navigation', icon: '📈', description: 'View telemetry', action: '/analytics', actionType: 'navigate' },
    { id: 'nav-settings', label: 'Settings', category: 'navigation', icon: '⚙️', description: 'Configure NEXUS', action: '/settings', actionType: 'navigate' },
];

// ============================================================================
// Collaboration Commands
// ============================================================================

const COLLABORATION_COMMANDS: Command[] = [
    { id: 'cmd-swarm', label: '/swarm', category: 'collaboration', icon: '🐝', description: 'Start swarm task', action: '/swarm', actionType: 'command' },
    { id: 'cmd-swarm-status', label: '/swarm-status', category: 'collaboration', icon: '📊', description: 'View swarm status', action: '/swarm-status', actionType: 'command' },
    { id: 'cmd-pool-stats', label: '/pool-stats', category: 'collaboration', icon: '📈', description: 'Agent pool statistics', action: '/pool-stats', actionType: 'command' },
];

// ============================================================================
// Evolution Commands
// ============================================================================

const EVOLUTION_COMMANDS: Command[] = [
    { id: 'cmd-evolve', label: '/evolve', category: 'evolution', icon: '🧬', description: 'Start evolution cycle', action: '/evolve', actionType: 'command' },
    { id: 'cmd-spawn', label: '/spawn', category: 'evolution', icon: '✨', description: 'Create new agent', action: '/spawn', actionType: 'command' },
    { id: 'cmd-agents', label: '/agents', category: 'evolution', icon: '🤖', description: 'List all agents', action: '/agents', actionType: 'command' },
    { id: 'cmd-specialize', label: '/specialize', category: 'evolution', icon: '🎯', description: 'Create specialized spinoff', action: '/specialize', actionType: 'command' },
    { id: 'cmd-review', label: '/review', category: 'evolution', icon: '👀', description: 'Review pending children', action: '/review', actionType: 'command' },
];

// ============================================================================
// Monitoring Commands
// ============================================================================

const MONITORING_COMMANDS: Command[] = [
    { id: 'cmd-budget', label: '/budget', category: 'monitoring', icon: '💰', description: 'Check budget status', action: '/budget', actionType: 'command' },
    { id: 'cmd-telemetry', label: '/telemetry', category: 'monitoring', icon: '📡', description: 'View telemetry report', action: '/telemetry', actionType: 'command' },
    { id: 'cmd-status', label: '/status', category: 'monitoring', icon: '📋', description: 'Orchestrator status', action: '/status', actionType: 'command' },
    { id: 'cmd-doctor', label: '/doctor', category: 'monitoring', icon: '🩺', description: 'System diagnostics', action: '/doctor', actionType: 'command' },
];

// ============================================================================
// Workspace Commands
// ============================================================================

const WORKSPACE_COMMANDS: Command[] = [
    { id: 'cmd-workspace', label: '/workspace', category: 'workspace', icon: '📁', description: 'Workspace info', action: '/workspace', actionType: 'command' },
    { id: 'cmd-bootstrap', label: '/bootstrap', category: 'workspace', icon: '🚀', description: 'Bootstrap project', action: '/bootstrap', actionType: 'command' },
];

// ============================================================================
// System Commands
// ============================================================================

const SYSTEM_COMMANDS: Command[] = [
    { id: 'cmd-help', label: '/help', category: 'system', icon: '❓', description: 'Show help', action: '/help', actionType: 'command' },
    { id: 'cmd-tutorial', label: '/tutorial', category: 'system', icon: '📖', description: 'Interactive tutorial', action: '/tutorial', actionType: 'command' },
    { id: 'cmd-chat', label: '/chat', category: 'system', icon: '💬', description: 'Chat-only mode', action: '/chat', actionType: 'command' },
    { id: 'cmd-reset', label: '/reset', category: 'system', icon: '🔄', description: 'Reset session', action: '/reset', actionType: 'command' },
];

// ============================================================================
// All Commands
// ============================================================================

export const ALL_COMMANDS: Command[] = [
    ...NAVIGATION_COMMANDS,
    ...COLLABORATION_COMMANDS,
    ...EVOLUTION_COMMANDS,
    ...MONITORING_COMMANDS,
    ...WORKSPACE_COMMANDS,
    ...SYSTEM_COMMANDS,
];

// ============================================================================
// Search Function
// ============================================================================

export function searchCommands(query: string): Command[] {
    if (!query.trim()) return ALL_COMMANDS.slice(0, 10); // Show top 10 by default

    const lowerQuery = query.toLowerCase();

    return ALL_COMMANDS.filter((cmd) => {
        // Match by label, description, or category
        return (
            cmd.label.toLowerCase().includes(lowerQuery) ||
            cmd.description.toLowerCase().includes(lowerQuery) ||
            cmd.category.toLowerCase().includes(lowerQuery)
        );
    }).slice(0, 15); // Limit results
}

// ============================================================================
// Category Labels
// ============================================================================

export const CATEGORY_LABELS: Record<Command['category'], string> = {
    navigation: 'Navigation',
    collaboration: 'Collaboration',
    evolution: 'Evolution',
    monitoring: 'Monitoring',
    workspace: 'Workspace',
    system: 'System',
};
