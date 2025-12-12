// NEXUS Dashboard Logic

// --- CONFIG ---
const API_BASE = ""; // Relative path
const WS_URL = `ws://${window.location.host}/ws/logs`;

// --- STATE ---
let cy = null;
let agents = [];

// --- INIT ---
document.addEventListener('DOMContentLoaded', () => {
    initGraph();
    fetchAgents();
    fetchFiles();
    connectWebSocket();
    setupUI();
});

// --- GRAPH (Cytoscape.js) ---
function initGraph() {
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#666',
                    'label': 'data(label)',
                    'color': '#fff',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'width': 60,
                    'height': 60,
                    'font-size': '12px'
                }
            },
            {
                selector: 'node[provider="gemini"]',
                style: { 'background-color': '#00f0ff', 'width': 80, 'height': 80 }
            },
            {
                selector: 'node[provider="claude"]',
                style: { 'background-color': '#ff9f1c', 'width': 80, 'height': 80 }
            },
            {
                selector: 'node[provider="spawned"]',
                style: { 'background-color': '#bd34fe' }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#555',
                    'target-arrow-color': '#555',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier'
                }
            }
        ],
        layout: {
            name: 'cose', // Force-directed layout
            animate: true
        }
    });

    cy.on('tap', 'node', function (evt) {
        const node = evt.target;
        showAgentDetails(node.data());
    });
}

async function fetchAgents() {
    try {
        const response = await fetch(`${API_BASE}/api/agents`);
        agents = await response.json();
        updateGraph(agents);
    } catch (error) {
        console.error("Failed to fetch agents:", error);
        logToTerminal("Error fetching agents: " + error.message, "error");
    }
}

function updateGraph(agentList) {
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

    // Add Edges (Simulated for Prototype)
    // In a real app, we'd fetch active interactions
    const edges = [];
    // Connect everyone to Gemini/Claude (Hub & Spoke)
    agentList.forEach(a => {
        if (a.id !== 'gemini' && a.id !== 'claude') {
            edges.push({ data: { source: 'gemini', target: a.id } });
        }
    });
    // Connect Gemini <-> Claude
    edges.push({ data: { source: 'gemini', target: 'claude' } });

    cy.add(edges);
    cy.layout({ name: 'cose', animate: true }).run();
}

// --- CODE MAP (V9.1) ---
let codeMapVisible = false;

async function toggleCodeMap() {
    codeMapVisible = !codeMapVisible;
    const btn = document.getElementById('btn-code-map');
    if (btn) btn.classList.toggle('active');

    if (codeMapVisible) {
        try {
            const response = await fetch(`${API_BASE}/api/dependencies`);
            const data = await response.json();
            renderCodeMap(data);
        } catch (e) {
            console.error(e);
        }
    } else {
        // Remove code nodes
        cy.elements('[type="code"]').remove();
        cy.layout({ name: 'cose', animate: true }).run();
    }
}

function renderCodeMap(data) {
    const nodes = data.nodes.map(n => ({
        data: { id: n, label: n, type: 'code' }
    }));

    const edges = data.edges.map(e => ({
        data: { source: e.source, target: e.target, type: 'code' }
    }));

    cy.add(nodes);
    cy.add(edges);

    // Style code nodes
    cy.style()
        .selector('node[type="code"]')
        .style({
            'background-color': '#333',
            'width': 20,
            'height': 20,
            'font-size': '8px',
            'label': 'data(label)'
        })
        .selector('edge[type="code"]')
        .style({
            'line-color': '#333',
            'target-arrow-color': '#333',
            'width': 1,
            'line-style': 'dashed'
        })
        .update();

    cy.layout({ name: 'cose', animate: true }).run();
}

function showAgentDetails(data) {
    const container = document.getElementById('agent-details');
    container.innerHTML = `
        <h3>${data.label}</h3>
        <p><strong>ID:</strong> ${data.id}</p>
        <p><strong>Provider:</strong> ${data.provider}</p>
        <p><strong>Capabilities:</strong></p>
        <ul>
            ${data.capabilities.map(c => `<li>${c}</li>`).join('')}
        </ul>
    `;
}

// --- FILE EXPLORER ---
async function fetchFiles() {
    try {
        const response = await fetch(`${API_BASE}/api/files`);
        const files = await response.json();
        const container = document.getElementById('file-explorer');
        container.innerHTML = ''; // Clear loading
        container.appendChild(createFileTree(files));
    } catch (error) {
        console.error("Failed to fetch files:", error);
    }
}

function createFileTree(node) {
    const div = document.createElement('div');
    div.className = 'file-node';

    const icon = document.createElement('i');
    icon.className = node.type === 'directory' ? 'fa-solid fa-folder folder' : 'fa-solid fa-file';
    div.appendChild(icon);

    const span = document.createElement('span');
    span.textContent = " " + node.name;
    div.appendChild(span);

    if (node.children && node.children.length > 0) {
        const childrenContainer = document.createElement('div');
        childrenContainer.style.display = 'none'; // Collapsed by default
        childrenContainer.style.marginLeft = '10px';

        node.children.forEach(child => {
            childrenContainer.appendChild(createFileTree(child));
        });

        div.onclick = (e) => {
            e.stopPropagation();
            const isHidden = childrenContainer.style.display === 'none';
            childrenContainer.style.display = isHidden ? 'block' : 'none';
            icon.className = isHidden ? 'fa-solid fa-folder-open folder' : 'fa-solid fa-folder folder';
        };
        div.appendChild(childrenContainer);
    }

    return div;
}

// --- WEBSOCKET LOGS ---
function connectWebSocket() {
    const ws = new WebSocket(WS_URL);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'log') {
            logToTerminal(data.content, 'system');
        }
        else if (data.type === 'TASK_STARTED') {
            logToTerminal(`🚀 TASK STARTED: ${data.data.task}`, 'system');
            // Pulse center
        }
        else if (data.type === 'TOOL_USE') {
            const agentId = data.data.agent.toLowerCase();
            logToTerminal(`🛠️ ${data.data.agent} uses ${data.data.tool}`, 'agent');
            pulseNode(agentId);
        }
        else if (data.type === 'TASK_COMPLETED') {
            logToTerminal(`✅ TASK COMPLETED`, 'system');
        }
        else if (data.type === 'FILE_EVENT') {
            logToTerminal(`📂 FILE ${data.event.toUpperCase()}: ${data.path}`, 'system');
            fetchFiles(); // Refresh tree
        }
    };

    ws.onclose = () => {
        setTimeout(connectWebSocket, 3000); // Reconnect
    };
}

function pulseNode(agentId) {
    if (!cy) return;
    const node = cy.$(`#${agentId}`);
    if (node) {
        node.animate({
            style: { 'width': 100, 'height': 100, 'border-width': 4, 'border-color': '#fff' }
        }, {
            duration: 200,
            complete: () => {
                node.animate({
                    style: { 'width': 80, 'height': 80, 'border-width': 0 }
                }, { duration: 200 });
            }
        });
    }
}

function logToTerminal(message, type = 'system') {
    const container = document.getElementById('log-container');
    const div = document.createElement('div');
    div.className = `log-entry ${type}`;
    div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight; // Auto-scroll
}

// --- UI UTILS ---
function setupUI() {
    const toggleBtn = document.getElementById('toggle-contrast');
    toggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('high-contrast');
    });
}
