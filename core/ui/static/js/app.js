// NEXUS V9.0 "Singularity" Dashboard Logic

// --- CONFIG ---
const API_BASE = ""; // Relative path
const WS_URL = `ws://${window.location.host}/ws/logs`;

// --- STATE ---
let cy = null;
let agents = [];
let controlPanelVisible = true; // Always visible in Cockpit mode

// --- INIT ---
document.addEventListener('DOMContentLoaded', () => {
    initGraph();
    fetchAgents();
    fetchFiles();
    connectWebSocket();
    setupUI();
    setupChat();

    // Start polling for telemetry
    setInterval(updateTelemetry, 2000);
    updateTelemetry(); // Initial call

    // Workspace Init
    initWorkspaces();
});

// --- GRAPH (Cytoscape.js) ---
function initGraph() {
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#333',
                    'label': 'data(label)',
                    'color': '#fff',
                    'text-valign': 'bottom',
                    'text-halign': 'center',
                    'text-margin-y': 5,
                    'width': 40,
                    'height': 40,
                    'font-size': '10px',
                    'border-width': 1,
                    'border-color': 'rgba(255,255,255,0.2)'
                }
            },
            {
                selector: 'node[provider="gemini"]',
                style: {
                    'background-color': '#00f3ff',
                    'width': 60,
                    'height': 60,
                    'border-color': '#00f3ff',
                    'border-width': 2,
                    'shadow-blur': 10,
                    'shadow-color': '#00f3ff'
                }
            },
            {
                selector: 'node[provider="claude"]',
                style: {
                    'background-color': '#ff9f1c',
                    'width': 60,
                    'height': 60,
                    'border-color': '#ff9f1c',
                    'border-width': 2,
                    'shadow-blur': 10,
                    'shadow-color': '#ff9f1c'
                }
            },
            {
                selector: 'node[provider="spawned"]',
                style: {
                    'background-color': '#bc13fe',
                    'border-color': '#bc13fe',
                    'shadow-blur': 10,
                    'shadow-color': '#bc13fe'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 1,
                    'line-color': 'rgba(255,255,255,0.1)',
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'none'
                }
            },
            {
                selector: '.active-edge',
                style: {
                    'width': 3,
                    'line-color': '#00f3ff',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': '#00f3ff',
                    'transition-property': 'line-color, width',
                    'transition-duration': '0.3s'
                }
            }
        ],
        layout: {
            name: 'cose', // Force-directed layout
            animate: true,
            randomize: false,
            componentSpacing: 100,
            nodeRepulsion: 400000,
            edgeElasticity: 100,
            nestingFactor: 5,
        }
    });

    cy.on('tap', 'node', function (evt) {
        const node = evt.target;
        // showAgentDetails(node.data()); // TODO: Implement details modal
        logToTerminal(`🔍 Inspecting Agent: ${node.data('label')}`, 'system');
    });
}

async function fetchAgents() {
    try {
        const response = await fetch(`${API_BASE}/api/agents`);
        agents = await response.json();
        updateGraph(agents);
        updateAgentList(agents);
    } catch (error) {
        console.error("Failed to fetch agents:", error);
        logToTerminal("Error fetching agents: " + error.message, "error");
    }
}

function updateGraph(agentList) {
    // Diff update to preserve positions if possible
    // For now, simple rebuild
    cy.elements().remove();

    // Add Nodes
    const nodes = agentList.map(a => ({
        data: {
            id: a.id,
            label: a.name,
            provider: a.provider,
            capabilities: a.capabilities
        }
    }));
    cy.add(nodes);

    // Update node count
    document.getElementById('node-count').textContent = nodes.length;

    // Add Edges (Hub & Spoke for visualization)
    const edges = [];
    agentList.forEach(a => {
        if (a.id !== 'gemini' && a.id !== 'claude') {
            // Connect spawned agents to their creator (assumed Gemini/Claude for now)
            edges.push({ data: { source: 'gemini', target: a.id } });
        }
    });
    // Connect Gemini <-> Claude (The Core Pair)
    edges.push({ data: { source: 'gemini', target: 'claude' } });

    cy.add(edges);
    cy.layout({ name: 'cose', animate: true }).run();
}

function updateAgentList(agentList) {
    const container = document.getElementById('agent-list');
    container.innerHTML = '';

    agentList.forEach(a => {
        const div = document.createElement('div');
        div.style.padding = '4px 8px';
        div.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
        div.style.fontSize = '0.85rem';
        div.style.display = 'flex';
        div.style.alignItems = 'center';

        const color = a.provider === 'gemini' ? '#00f3ff' : (a.provider === 'claude' ? '#ff9f1c' : '#bc13fe');

        div.innerHTML = `
            <div style="width: 8px; height: 8px; border-radius: 50%; background: ${color}; margin-right: 8px; box-shadow: 0 0 5px ${color};"></div>
            <span>${a.name}</span>
        `;
        container.appendChild(div);
    });
}

// --- TELEMETRY ---
async function updateTelemetry() {
    // CPU/Mem (Mock for now, or fetch from /api/doctor if enhanced)
    // In a real app, we'd have a dedicated /api/telemetry/stats endpoint

    // Fetch Budget
    try {
        const res = await fetch(`${API_BASE}/api/budget`);
        const data = await res.json();
        if (!data.error) {
            const spent = data.total_cost || 0;
            document.getElementById('token-count').textContent = `$${spent.toFixed(4)}`;
        }
    } catch (e) { }

    // Mock CPU/Mem removed - waiting for SYSTEM_STATS event
    // const cpu = Math.floor(Math.random() * 10) + 5; // 5-15% idle
    // const mem = Math.floor(Math.random() * 50) + 200; // 200-250MB
    // document.getElementById('cpu-usage').textContent = `${cpu}%`;
    // document.getElementById('mem-usage').textContent = `${mem} MB`;
}

// --- FILE EXPLORER ---
async function fetchFiles() {
    try {
        const response = await fetch(`${API_BASE}/api/files`);
        const files = await response.json();
        const container = document.getElementById('file-tree');
        container.innerHTML = '';
        container.appendChild(createFileTree(files));

        // Count files
        const count = countFiles(files);
        document.getElementById('file-count').textContent = `${count} Files`;
    } catch (error) {
        console.error("Failed to fetch files:", error);
    }
}

function countFiles(node) {
    if (node.type === 'file') return 1;
    if (node.children) {
        return node.children.reduce((acc, child) => acc + countFiles(child), 0);
    }
    return 0;
}

function createFileTree(node) {
    const div = document.createElement('div');
    div.className = 'file-node';
    div.style.padding = '2px 0';
    div.style.cursor = 'pointer';
    div.style.whiteSpace = 'nowrap';
    div.style.overflow = 'hidden';
    div.style.textOverflow = 'ellipsis';

    const icon = document.createElement('i');
    // Simple ASCII or FontAwesome if available
    // Using unicode for simplicity if FA fails
    icon.style.marginRight = '5px';
    icon.style.width = '15px';
    icon.style.display = 'inline-block';
    icon.style.textAlign = 'center';

    if (node.type === 'directory') {
        icon.textContent = '📁';
        icon.style.color = '#ffd700';
    } else {
        icon.textContent = '📄';
        icon.style.color = '#a0a0a0';
        if (node.name.endsWith('.py')) icon.style.color = '#3572A5';
        if (node.name.endsWith('.js')) icon.style.color = '#f1e05a';
        if (node.name.endsWith('.css')) icon.style.color = '#563d7c';
        if (node.name.endsWith('.md')) icon.style.color = '#e34c26';
    }

    div.appendChild(icon);

    const span = document.createElement('span');
    span.textContent = node.name;
    span.style.fontSize = '0.85rem';
    span.style.color = 'var(--text-secondary)';
    div.appendChild(span);

    if (node.children && node.children.length > 0) {
        const childrenContainer = document.createElement('div');
        childrenContainer.style.display = 'none'; // Collapsed by default
        childrenContainer.style.marginLeft = '12px';
        childrenContainer.style.borderLeft = '1px solid rgba(255,255,255,0.05)';

        node.children.forEach(child => {
            childrenContainer.appendChild(createFileTree(child));
        });

        div.onclick = (e) => {
            e.stopPropagation();
            const isHidden = childrenContainer.style.display === 'none';
            childrenContainer.style.display = isHidden ? 'block' : 'none';
            icon.textContent = isHidden ? '📂' : '📁';
        };
        div.appendChild(childrenContainer);
    }

    return div;
}

// --- WEBSOCKET LOGS ---
function connectWebSocket() {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        logToTerminal("🔌 Connected to NEXUS Core", "success");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'log') {
            logToTerminal(data.content, 'system');
        }
        else if (data.type === 'TASK_STARTED') {
            logToTerminal(`🚀 TASK STARTED: ${data.data.task}`, 'info');
            // Pulse center
        }
        else if (data.type === 'TOOL_USE') {
            const agentId = data.data.agent.toLowerCase();
            logToTerminal(`🛠️ ${data.data.agent} uses ${data.data.tool}`, 'info');
            pulseNode(agentId);
            animateEdge(agentId, 'gemini'); // Visualize comms
        }
        else if (data.type === 'AGENT_TALK') {
            const from = data.data.sender.toLowerCase();
            const to = data.data.receiver ? data.data.receiver.toLowerCase() : 'gemini';
            logToTerminal(`💬 ${data.data.sender} -> ${data.data.receiver || 'All'}`, 'info');
            animateEdge(from, to);
        }
        else if (data.type === 'TASK_COMPLETED') {
            logToTerminal(`✅ TASK COMPLETED`, 'success');
        }
        else if (data.type === 'FILE_EVENT') {
            logToTerminal(`📂 FILE ${data.event.toUpperCase()}: ${data.path}`, 'system');
            fetchFiles(); // Refresh tree
        }
        else if (data.type === 'SWARM_NEGOTIATION') {
            // Visualize negotiation
            const agent = data.data.agent || "Unknown";
            logToTerminal(`🤝 [NEGOTIATION] ${agent}: ${data.data.content.substring(0, 50)}...`, 'info');
            pulseNode(agent.toLowerCase());
        }
        else if (data.type === 'SWARM_EXECUTION') {
            // Visualize execution
            const agent = data.data.agent_id || "Unknown";
            logToTerminal(`⚙️ [EXECUTION] ${agent}: ${data.data.content.substring(0, 50)}...`, 'info');
            pulseNode(agent.toLowerCase());
        }
        else if (data.type === 'WORKSPACE_SWITCHED') {
            logToTerminal(`🔄 Workspace Switched: ${data.name}`, 'system');
            fetchFiles();
            fetchAgents();
            initWorkspaces(); // Refresh list
        }
        else if (data.type === 'HIVE_MIND_STATE_CHANGE') {
            const oldState = data.data.old.replace('hive_', '').toUpperCase();
            const newState = data.data.new.replace('hive_', '').toUpperCase();
            logToTerminal(`🐝 HIVE MIND: ${oldState} ➔ ${newState}`, 'success');

            // Visual feedback
            const cy = window.cy;
            if (cy) {
                cy.nodes().animate({
                    style: { 'border-color': '#FFD700', 'border-width': 4 }
                }, { duration: 500 }).animate({
                    style: { 'border-color': '#666', 'border-width': 1 }
                }, { duration: 500 });
            }
        }
        else if (data.type === 'SYSTEM_STATS') {
            // Real Telemetry from Core
            const stats = data.data;
            if (stats.cpu_percent !== undefined) {
                document.getElementById('cpu-usage').textContent = `${stats.cpu_percent.toFixed(1)}%`;
            }
            if (stats.memory_used_mb !== undefined) {
                document.getElementById('mem-usage').textContent = `${Math.round(stats.memory_used_mb)} MB`;
            }
        }
        else if (data.type === 'AGENTS_UPDATED') {
            logToTerminal(`👥 Agents Updated: ${data.data.count} active`, 'system');
            fetchAgents(); // Refresh graph
        }
    };

    ws.onclose = () => {
        logToTerminal("🔌 Disconnected. Reconnecting...", "warn");
        setTimeout(connectWebSocket, 3000); // Reconnect
    };
}

function pulseNode(agentId) {
    if (!cy) return;
    const node = cy.$(`#${agentId}`);
    if (node && node.length > 0) {
        node.animate({
            style: { 'width': 80, 'height': 80, 'border-width': 4, 'border-color': '#fff' }
        }, {
            duration: 200,
            complete: () => {
                node.animate({
                    style: { 'width': 60, 'height': 60, 'border-width': 2 }
                }, { duration: 200 });
            }
        });
    }
}

function animateEdge(sourceId, targetId) {
    if (!cy) return;
    // Find or create edge
    let edge = cy.$(`edge[source="${sourceId}"][target="${targetId}"]`);
    if (edge.length === 0) {
        // Try reverse
        edge = cy.$(`edge[source="${targetId}"][target="${sourceId}"]`);
    }

    if (edge.length > 0) {
        edge.addClass('active-edge');
        setTimeout(() => edge.removeClass('active-edge'), 500);
    }
}

function logToTerminal(message, type = 'system') {
    const container = document.getElementById('log-container');
    const div = document.createElement('div');
    div.className = `log-entry log-${type}`;
    div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight; // Auto-scroll
}

// --- CHAT IPC ---
function setupChat() {
    const input = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');

    input.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            const text = input.value.trim();
            if (!text) return;

            // Add to UI
            const msgDiv = document.createElement('div');
            msgDiv.style.marginBottom = '4px';
            msgDiv.innerHTML = `<span style="color: var(--neon-blue);">You:</span> ${text}`;
            messages.appendChild(msgDiv);
            messages.scrollTop = messages.scrollHeight;

            input.value = '';

            // Send to backend
            try {
                await fetch(`${API_BASE}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: text })
                });
            } catch (err) {
                logToTerminal(`Chat Error: ${err.message}`, 'error');
            }
        }
    });
}

// --- UI UTILS ---
function setupUI() {
    // Buttons
    document.getElementById('btn-evolve').onclick = () => {
        if (confirm("Trigger Evolution?")) {
            fetch(`${API_BASE}/api/evolve/trigger`, { method: 'POST' });
            logToTerminal("🧬 Evolution Triggered", "system");
        }
    };

    document.getElementById('btn-spawn').onclick = () => {
        const modal = document.getElementById('modal-overlay');
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="glass-panel" style="width: 400px; padding: 20px; margin: auto; background: rgba(0,0,0,0.9);">
                <h3 style="color: var(--neon-blue); margin-top: 0;">Spawn New Agent</h3>
                <input type="text" id="spawn-name" placeholder="Agent Name (e.g. 'Coder')" style="width: 100%; padding: 8px; margin-bottom: 10px; background: #222; border: 1px solid #444; color: white;">
                <textarea id="spawn-prompt" placeholder="System Prompt..." style="width: 100%; height: 100px; padding: 8px; margin-bottom: 10px; background: #222; border: 1px solid #444; color: white;"></textarea>
                <div style="display: flex; justify-content: flex-end; gap: 10px;">
                    <button class="btn-neon danger" onclick="document.getElementById('modal-overlay').style.display='none'">Cancel</button>
                    <button class="btn-neon" id="confirm-spawn">Spawn</button>
                </div>
            </div>
        `;

        document.getElementById('confirm-spawn').onclick = async () => {
            const name = document.getElementById('spawn-name').value;
            const prompt = document.getElementById('spawn-prompt').value;
            if (!name) return;

            logToTerminal(`🤖 Spawning Agent: ${name}...`, "system");
            try {
                const res = await fetch(`${API_BASE}/api/agents`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, system_prompt: prompt, capabilities: ['reasoning', 'coding'] })
                });
                const data = await res.json();
                if (data.status === 'created') {
                    logToTerminal(`✅ Agent Spawned: ${name}`, "success");
                    fetchAgents(); // Refresh list
                } else {
                    logToTerminal(`❌ Spawn Failed: ${data.error}`, "error");
                }
            } catch (e) {
                logToTerminal(`❌ Error: ${e.message}`, "error");
            }
            modal.style.display = 'none';
        };
    };

    document.getElementById('btn-swarm').onclick = () => {
        const task = prompt("Enter Swarm Task:");
        if (task) {
            fetch(`${API_BASE}/api/swarm/trigger`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task })
            });
            logToTerminal(`🐝 Swarm Task Queued: ${task}`, "system");
        }
    };

    document.getElementById('btn-stop').onclick = () => {
        if (confirm("EMERGENCY STOP?")) {
            fetch(`${API_BASE}/api/stop`, { method: 'POST' });
            logToTerminal("🛑 STOP SIGNAL SENT", "error");
        }
    };
}

// --- WORKSPACE MANAGEMENT ---
async function initWorkspaces() {
    const select = document.getElementById('workspace-select');
    const btnNew = document.getElementById('btn-new-workspace');

    // Load workspaces
    try {
        const res = await fetch(`${API_BASE}/api/workspaces`);
        const workspaces = await res.json();

        select.innerHTML = '';
        workspaces.forEach(ws => {
            const opt = document.createElement('option');
            opt.value = ws.name;
            opt.textContent = ws.name + (ws.is_current ? " (Active)" : "");
            if (ws.is_current) opt.selected = true;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error("Failed to load workspaces", e);
    }

    // Switch handler
    select.onchange = async () => {
        const name = select.value;
        if (confirm(`Switch to workspace '${name}'? Current state will be saved.`)) {
            logToTerminal(`🔄 Switching to ${name}...`, "system");
            await fetch(`${API_BASE}/api/workspaces/switch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            // Page reload might be needed or just let WS event handle it
            setTimeout(() => window.location.reload(), 1000);
        }
    };

    // New Workspace handler
    btnNew.onclick = async () => {
        const name = prompt("New Workspace Name (leave empty for auto-generated):");
        if (name !== null) {
            logToTerminal(`✨ Creating workspace...`, "system");
            const res = await fetch(`${API_BASE}/api/workspaces`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const data = await res.json();
            if (data.status === 'created') {
                logToTerminal(`✅ Workspace created: ${data.name}`, "success");
                initWorkspaces(); // Refresh list
                // Optionally switch immediately
                if (confirm("Switch to new workspace now?")) {
                    select.value = data.name;
                    select.onchange();
                }
            } else {
                logToTerminal(`❌ Error: ${data.error}`, "error");
            }
        }
    };
}
