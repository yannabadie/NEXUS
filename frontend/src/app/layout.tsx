import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NEXUS Dashboard - Collaborative AI Intelligence",
  description: "Real-time dashboard for NEXUS multi-agent orchestration system. Monitor HiveMind, Swarm, and Agent-as-Tool in action.",
  keywords: ["NEXUS", "AI", "Multi-Agent", "HiveMind", "Swarm", "Dashboard"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-zinc-950 text-zinc-100 min-h-screen`}
      >
        <div className="flex flex-col min-h-screen">
          {/* Header */}
          <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-50">
            <div className="container mx-auto px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">N</span>
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-white">NEXUS</h1>
                  <p className="text-xs text-zinc-400">Collaborative Intelligence</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-sm text-zinc-400">Connected</span>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1 container mx-auto px-4 py-6">
            {children}
          </main>

          {/* Footer */}
          <footer className="border-t border-zinc-800 bg-zinc-900/30 py-3">
            <div className="container mx-auto px-4 text-center text-xs text-zinc-500">
              NEXUS V10 • HiveMind + Swarm + Agent-as-Tool • Created by Yann Abadie
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
