"use client";

export default function SettingsPage() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-white">⚙️ Settings</h1>
                <p className="text-sm text-zinc-400">
                    Configure NEXUS behavior and preferences
                </p>
            </div>

            {/* Settings Sections */}
            <div className="space-y-6">
                {/* Budget Settings */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                    <h2 className="text-lg font-medium text-white mb-4">💰 Budget</h2>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm text-zinc-400 mb-2">
                                Daily Budget Limit ($)
                            </label>
                            <input
                                type="number"
                                defaultValue={50}
                                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                            />
                        </div>
                        <div className="flex items-center gap-3">
                            <input type="checkbox" id="budget-warning" defaultChecked className="rounded" />
                            <label htmlFor="budget-warning" className="text-sm text-zinc-300">
                                Show warning at 80% budget usage
                            </label>
                        </div>
                    </div>
                </div>

                {/* Swarm Settings */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                    <h2 className="text-lg font-medium text-white mb-4">🐝 Swarm Engine</h2>
                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <input type="checkbox" id="swarm-enabled" defaultChecked className="rounded" />
                            <label htmlFor="swarm-enabled" className="text-sm text-zinc-300">
                                Enable Swarm Mode for MODERATE+ tasks
                            </label>
                        </div>
                        <div className="flex items-center gap-3">
                            <input type="checkbox" id="swarm-negotiation" defaultChecked className="rounded" />
                            <label htmlFor="swarm-negotiation" className="text-sm text-zinc-300">
                                Enable agent negotiation
                            </label>
                        </div>
                        <div>
                            <label className="block text-sm text-zinc-400 mb-2">
                                Default Swarm Mode
                            </label>
                            <select className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white focus:border-violet-500 focus:outline-none">
                                <option value="ping_pong">Ping-Pong</option>
                                <option value="parallel">Parallel</option>
                                <option value="sequential">Sequential</option>
                                <option value="lead_support">Lead/Support</option>
                                <option value="specialist">Specialist</option>
                                <option value="red_blue">Red/Blue</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Evolution Settings */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                    <h2 className="text-lg font-medium text-white mb-4">🧬 Evolution</h2>
                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <input type="checkbox" id="auto-promotion" className="rounded" />
                            <label htmlFor="auto-promotion" className="text-sm text-zinc-300">
                                Auto-promote successful children
                            </label>
                        </div>
                        <div>
                            <label className="block text-sm text-zinc-400 mb-2">
                                Max Generations per Day
                            </label>
                            <input
                                type="number"
                                defaultValue={3}
                                min={1}
                                max={10}
                                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white focus:border-violet-500 focus:outline-none"
                            />
                        </div>
                    </div>
                </div>

                {/* UI Settings */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                    <h2 className="text-lg font-medium text-white mb-4">🎨 Interface</h2>
                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <input type="checkbox" id="verbose-mode" defaultChecked className="rounded" />
                            <label htmlFor="verbose-mode" className="text-sm text-zinc-300">
                                Verbose output in chat
                            </label>
                        </div>
                        <div className="flex items-center gap-3">
                            <input type="checkbox" id="auto-scroll" defaultChecked className="rounded" />
                            <label htmlFor="auto-scroll" className="text-sm text-zinc-300">
                                Auto-scroll agent exchanges
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end">
                <button
                    className="px-6 py-2 bg-violet-600 hover:bg-violet-700 rounded-lg text-sm font-medium text-white transition-colors"
                    onClick={() => alert("Settings saved! (coming soon)")}
                >
                    Save Settings
                </button>
            </div>
        </div>
    );
}
