/**
 * NEXUS API Client
 * Connects to the FastAPI backend at port 8000
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiResponse<T> {
    data?: T;
    error?: string;
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...options?.headers,
            },
        });

        if (!response.ok) {
            return { error: `HTTP ${response.status}: ${response.statusText}` };
        }

        const data = await response.json();
        return { data };
    } catch (error) {
        return { error: error instanceof Error ? error.message : "Unknown error" };
    }
}

// ============================================================================
// Agent APIs
// ============================================================================

export interface Agent {
    id: string;
    name: string;
    provider: string;
    capabilities: string[];
    domains: string[];
    status: "active" | "idle" | "spawned";
}

export async function getAgents() {
    return fetchApi<Agent[]>("/api/agents");
}

export async function createAgent(agentData: {
    name: string;
    mission: string;
    capabilities: string[];
}) {
    return fetchApi<Agent>("/api/agents", {
        method: "POST",
        body: JSON.stringify(agentData),
    });
}

// ============================================================================
// Orchestration APIs
// ============================================================================

export interface OrchestrationState {
    fsm_state: string;
    swarm_mode: string | null;
    hive_mind_phase: number | null;
    active_agent: string;
    session_uuid: string | null;
}

export async function getOrchestrationState() {
    return fetchApi<OrchestrationState>("/api/orchestration");
}

// ============================================================================
// Self-Awareness APIs
// ============================================================================

export interface SelfAwareness {
    capabilities: string[];
    current_state: string;
    active_agents: string[];
    swarm_mode: string | null;
    hive_mind_phase: number | null;
    budget_remaining: number;
    last_task: string | null;
}

export async function getSelfAwareness() {
    return fetchApi<SelfAwareness>("/api/self-awareness");
}

// ============================================================================
// Evolution APIs
// ============================================================================

export interface EvolutionStatus {
    generation: number;
    children_count: number;
    mutation_success_rate: number;
    last_evolution: string | null;
}

export async function getEvolutionStatus() {
    return fetchApi<EvolutionStatus>("/api/evolution/status");
}

// ============================================================================
// Budget APIs
// ============================================================================

export interface BudgetStatus {
    spent: number;
    limit: number;
    remaining: number;
    percentage: number;
}

export async function getBudgetStatus() {
    return fetchApi<BudgetStatus>("/api/budget");
}

// ============================================================================
// Chat APIs
// ============================================================================

export async function sendChatMessage(message: string) {
    return fetchApi<{ response: string }>("/api/chat", {
        method: "POST",
        body: JSON.stringify({ message }),
    });
}

// ============================================================================
// Control APIs
// ============================================================================

export async function triggerEvolve() {
    return fetchApi<{ status: string }>("/api/control/evolve", { method: "POST" });
}

export async function triggerSwarm(task: string) {
    return fetchApi<{ status: string }>("/api/control/swarm", {
        method: "POST",
        body: JSON.stringify({ task }),
    });
}

export async function triggerStop() {
    return fetchApi<{ status: string }>("/api/control/stop", { method: "POST" });
}
