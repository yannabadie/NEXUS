/**
 * NEXUS Design System Tokens
 * 
 * Centralized design tokens for consistent styling across the dashboard.
 * Based on UI_UX_PROPOSAL.md specification.
 */

// ============================================================================
// Agent Colors
// ============================================================================

export const AGENT_COLORS = {
    gemini: {
        primary: '#3B82F6',
        gradient: 'from-blue-500 to-cyan-500',
        bg: 'bg-blue-500',
        bgLight: 'bg-blue-500/20',
        border: 'border-blue-500',
        text: 'text-blue-400',
    },
    claude: {
        primary: '#F97316',
        gradient: 'from-orange-500 to-amber-500',
        bg: 'bg-orange-500',
        bgLight: 'bg-orange-500/20',
        border: 'border-orange-500',
        text: 'text-orange-400',
    },
    spawned: {
        primary: '#8B5CF6',
        gradient: 'from-violet-500 to-fuchsia-500',
        bg: 'bg-violet-500',
        bgLight: 'bg-violet-500/20',
        border: 'border-violet-500',
        text: 'text-violet-400',
    },
} as const;

// ============================================================================
// Status Colors
// ============================================================================

export const STATUS_COLORS = {
    success: {
        bg: 'bg-emerald-500',
        bgLight: 'bg-emerald-500/20',
        text: 'text-emerald-400',
        border: 'border-emerald-500',
    },
    warning: {
        bg: 'bg-yellow-500',
        bgLight: 'bg-yellow-500/20',
        text: 'text-yellow-400',
        border: 'border-yellow-500',
    },
    error: {
        bg: 'bg-red-500',
        bgLight: 'bg-red-500/20',
        text: 'text-red-400',
        border: 'border-red-500',
    },
    info: {
        bg: 'bg-cyan-500',
        bgLight: 'bg-cyan-500/20',
        text: 'text-cyan-400',
        border: 'border-cyan-500',
    },
    pending: {
        bg: 'bg-zinc-500',
        bgLight: 'bg-zinc-500/20',
        text: 'text-zinc-400',
        border: 'border-zinc-500',
    },
} as const;

// ============================================================================
// HiveMind Phase Colors
// ============================================================================

export const PHASE_COLORS = {
    analysis: { bg: 'bg-indigo-500', text: 'text-indigo-400', icon: '🔍' },
    debate: { bg: 'bg-pink-500', text: 'text-pink-400', icon: '⚔️' },
    architecture: { bg: 'bg-teal-500', text: 'text-teal-400', icon: '📐' },
    execution: { bg: 'bg-amber-500', text: 'text-amber-400', icon: '⚡' },
    diagnosis: { bg: 'bg-red-500', text: 'text-red-400', icon: '🔬' },
    retry: { bg: 'bg-violet-500', text: 'text-violet-400', icon: '🔄' },
    consolidation: { bg: 'bg-emerald-500', text: 'text-emerald-400', icon: '📦' },
} as const;

// ============================================================================
// Navigation Items
// ============================================================================

export const NAV_ITEMS = [
    { id: 'dashboard', icon: '📊', label: 'Dashboard', href: '/' },
    { id: 'chat', icon: '💬', label: 'Chat', href: '/chat' },
    { id: 'hivemind', icon: '🐝', label: 'HiveMind', href: '/hivemind' },
    { id: 'agents', icon: '🤖', label: 'Agents', href: '/agents' },
    { id: 'analytics', icon: '📈', label: 'Analytics', href: '/analytics' },
    { id: 'settings', icon: '⚙️', label: 'Settings', href: '/settings' },
] as const;

// ============================================================================
// Swarm Mode Icons
// ============================================================================

export const SWARM_MODES = {
    parallel: { icon: '⚡', label: 'Parallel', description: 'Independent subtasks' },
    sequential: { icon: '📋', label: 'Sequential', description: 'Ordered steps' },
    lead_support: { icon: '👑', label: 'Lead/Support', description: 'Expert-dominated' },
    ping_pong: { icon: '🏓', label: 'Ping-Pong', description: 'Rapid iteration' },
    specialist: { icon: '🎯', label: 'Specialist', description: 'Single expert' },
    red_blue: { icon: '⚔️', label: 'Red/Blue', description: 'Adversarial review' },
} as const;

// ============================================================================
// Badge Variants
// ============================================================================

export const BADGE_VARIANTS = {
    default: 'bg-zinc-700 text-zinc-300',
    primary: 'bg-violet-600/20 border border-violet-600 text-violet-300',
    success: 'bg-emerald-600/20 border border-emerald-600 text-emerald-300',
    warning: 'bg-yellow-600/20 border border-yellow-600 text-yellow-300',
    error: 'bg-red-600/20 border border-red-600 text-red-300',
} as const;

// ============================================================================
// Animation Classes
// ============================================================================

export const ANIMATIONS = {
    fadeIn: 'animate-fadeIn',
    pulse: 'animate-pulse',
    spin: 'animate-spin',
    bounce: 'animate-bounce',
} as const;

// ============================================================================
// Type Exports
// ============================================================================

export type AgentType = keyof typeof AGENT_COLORS;
export type StatusType = keyof typeof STATUS_COLORS;
export type PhaseType = keyof typeof PHASE_COLORS;
export type SwarmModeType = keyof typeof SWARM_MODES;
export type NavItemType = typeof NAV_ITEMS[number];
