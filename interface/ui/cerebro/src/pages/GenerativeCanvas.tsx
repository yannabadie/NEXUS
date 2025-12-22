import { useState, useEffect } from 'react';

// We need a way to dynamically import the generated component.
// In Vite, we can use `import.meta.glob`.
const generatedFiles = import.meta.glob('../components/generated/*.tsx');

export default function GenerativeCanvas() {
    const [Component, setComponent] = useState<React.ComponentType | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [generationCount, setGenerationCount] = useState(0);

    const simulateLogs = () => {
        setLogs([]);
        const messages = [
            "Initializing Quantum Core...",
            "Parsing Natural Language Intent...",
            "Synthesizing React Component Structure...",
            "Optimizing Tailwind Classnames...",
            "Hot-Swapping Module...",
            "Render Complete."
        ];

        messages.forEach((msg, i) => {
            setTimeout(() => {
                setLogs(prev => [...prev, `> ${msg}`]);
            }, i * 300);
        });
    };

    // PROMPT STATE
    const [prompt, setPrompt] = useState("Create a modern login page with glassmorphism effects");

    const generateUI = async () => {
        if (loading) return;
        setLoading(true);
        setError(null);
        setLogs(prev => [...prev, `> Initializing Interface with Core...`]);

        try {
            // 1. Call API
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Generation failed');
            }

            const data = await response.json();
            setLogs(prev => [...prev, `> Core: ${data.message}`]);
            setLogs(prev => [...prev, `> Hot-Swapping Module...`]);

            // 2. Wait a moment for Vite HMR to catch the file change (optional but safer)
            await new Promise(r => setTimeout(r, 500));

            // 3. Reload Component
            const path = '../components/generated/GeneratedComponent.tsx';

            // Force re-import
            // Note: In a real prod env, we'd use a dynamic import with a query param to bust cache, 
            // but import.meta.glob is static. Vite HMR should handle the update automatically.
            // We just trigger a re-render.
            setGenerationCount(c => c + 1);

            if (generatedFiles[path]) {
                const module: any = await generatedFiles[path]();
                setComponent(() => module.default);
            } else {
                throw new Error("Generated file not found in glob manifest");
            }

            setLogs(prev => [...prev, `> Render Complete.`]);

        } catch (err: any) {
            setError(err.message);
            setLogs(prev => [...prev, `> ERROR: ${err.message}`]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // Optional: Load existing if available, but don't auto-generate
        // loadLatestComponent(); 
    }, []);

    return (
        <div className="min-h-screen bg-nexus-darker p-8 font-sans text-white">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-8 flex items-center justify-between bg-nexus-dark/50 p-6 rounded-2xl border border-gray-800 backdrop-blur-md shadow-lg">
                    <div>
                        <h1 className="text-3xl font-bold mb-2 tracking-tight flex items-center gap-3">
                            Project <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-500">GENESIS</span>
                            <span className="text-xs font-mono bg-blue-500/10 text-blue-400 px-2 py-1 rounded border border-blue-500/20">V14.2 QUANTUM</span>
                        </h1>
                        <p className="text-gray-400">Generative UI Canvas (Local Prototype)</p>
                    </div>
                    <div className="flex gap-4 items-center">
                        <input
                            type="text"
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            className="bg-black/50 border border-gray-700 rounded-lg px-4 py-3 min-w-[300px] text-sm focus:outline-none focus:border-blue-500 transition-colors"
                            placeholder="Describe your UI..."
                        />
                        <button
                            onClick={generateUI}
                            disabled={loading}
                            className={`group relative px-6 py-3 bg-primary hover:bg-blue-600 rounded-lg text-white font-semibold transition-all shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_25px_rgba(59,130,246,0.6)] disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden`}
                        >
                            <span className="relative z-10 flex items-center gap-2">
                                <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                {loading ? 'Synthesizing...' : 'Regenerate UI'}
                            </span>
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-shimmer" />
                        </button>
                    </div>
                </div>

                {/* Canvas Area */}
                <div data-testid="canvas" className="bg-black border border-gray-800 rounded-3xl min-h-[600px] overflow-hidden relative shadow-2xl ring-1 ring-white/5">
                    {/* Background Grid */}
                    <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 pointer-events-none"></div>

                    {loading && (
                        <div data-testid="quantum-loader" className="absolute inset-0 flex flex-col items-center justify-center bg-black/95 z-20 backdrop-blur-md">
                            <div className="w-[500px] font-mono text-xs text-green-400 bg-gray-950 p-6 rounded-xl border border-green-500/30 shadow-[0_0_50px_rgba(34,197,94,0.1)] opacity-95">
                                <div className="text-gray-500 mb-4 border-b border-gray-800 pb-2 flex justify-between">
                                    <span>KERNEL: NEXUS_CORE_V8.4</span>
                                    <span>PID: {Math.floor(Math.random() * 9999)}</span>
                                </div>
                                {logs.map((log, i) => (
                                    <div key={i} className="mb-1 truncate animate-fade-in-up" style={{ animationDelay: `${i * 50}ms` }}>
                                        <span className="text-blue-500 mr-2">[{new Date().toLocaleTimeString()}]</span>
                                        {log}
                                    </div>
                                ))}
                                <div className="animate-pulse mt-2">_</div>
                            </div>
                        </div>
                    )}

                    {error ? (
                        <div className="flex flex-col items-center justify-center h-[600px] text-red-400 font-mono p-8 text-center bg-red-950/10">
                            <svg className="w-16 h-16 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <h3 className="text-lg font-bold mb-2">Generation Failed</h3>
                            <p className="text-sm opacity-80 max-w-md bg-black/50 p-4 rounded border border-red-500/20">{error}</p>
                        </div>
                    ) : Component ? (
                        <div key={generationCount} className="h-full animate-in fade-in zoom-in-95 duration-700">
                            <Component />
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-[600px] text-gray-500 font-mono">
                            <div className="w-4 h-4 rounded-full bg-blue-500 animate-ping mb-4"></div>
                            <span className="tracking-widest text-sm">[AWAITING QUANTUM SIGNAL]</span>
                        </div>
                    )}
                </div>

                {/* Console/Status */}
                <div className="mt-6 flex justify-between items-center text-xs font-mono text-gray-500 border-t border-gray-800 pt-4">
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                            System Status: ONLINE
                        </span>
                        <span className="text-gray-700">|</span>
                        <span>Latency: 14ms</span>
                    </div>
                    <div>
                        Mode: LOCAL_VERIFICATION_PROTOCOL
                    </div>
                </div>
            </div>
        </div>
    );
}
