"""
NEXUS Generative UI Core
Generates React 19 components based on natural language prompts.
Currently implements "Genesis v1" (Rule-based Template Engine) for local verification.
"""

import os
import asyncio
import textwrap
import logging
from typing import Optional
from pathlib import Path

# Cycle 011: Architecturally Correct Async Drivers
from core.config import load_config
from core.drivers.async_factory import AsyncDriverFactory

# Setup lightweight logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GenerativeCore")

class ComponentGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create output directory {output_dir}: {e}")
            raise

        # Cycle 011: Initialize Intelligence via Async Factory
        self.driver = None
        self.factory = None
        
        try:
            import shutil
            self.config = load_config()
            
            # DEEP DIVE FIX: Explicitly resolve CLI paths to avoid WinError 2
            # The shell=True in drivers implies PATH search, but explicit is safer
            claude_path = shutil.which("claude") or shutil.which("claude.cmd") or "claude"
            self.config.claude_cli_path = claude_path
            logger.info(f"Resolved Claude CLI path: {claude_path}")
            
            self.factory = AsyncDriverFactory(self.config, self.config.workspace_path)
            
            # Load System Prompt
            self.system_prompt_path = self.config.nexus_root / "core" / "prompts" / "ui_designer.md"
            if self.system_prompt_path.exists():
                self.system_prompt = self.system_prompt_path.read_text(encoding="utf-8")
            else:
                logger.warning("UI Designer prompt not found! Falling back to basic prompt.")
                self.system_prompt = "You are an expert React Engineer."
                
        except Exception as e:
            logger.error(f"Failed to initialize Intelligence Factory: {e}")

    async def _init_driver(self):
        """Lazy async initialization of the driver."""
        if self.driver: 
            return

        if not self.factory:
            raise RuntimeError("Factory not initialized")

        try:
            # Prefer Claude for Coding tasks (Best Practice V8.4.0)
            # Fallback to Gemini if Claude fails? For now, explicit Claude.
            # We could use UnifiedRegistry to lookup capability, but let's be direct for the Generator.
            logger.info("Initializing Async Claude Driver for UI Generation...")
            self.driver = self.factory.get_claude_driver() 
        except Exception as e:
            logger.error(f"Failed to get Async Driver: {e}")
            raise

    def validate_prompt(self, prompt: str) -> bool:
        """
        Validate input prompt for safety and quality.
        Reject empty, too short, or suspicious prompts.
        """
        if not prompt or not prompt.strip():
            logger.warning("Rejected empty prompt")
            return False
            
        if len(prompt.strip()) < 3:
            logger.warning(f"Rejected too short prompt: '{prompt}'")
            return False
            
        # Basic injection check (simple heuristic for MVP)
        # Full security should use core.security.input_guard
        if "ignore" in prompt.lower() and "instruction" in prompt.lower():
            logger.warning(f"Rejected potential injection: '{prompt}'")
            return False
            
        return True

    # Template: Modern Login Form
    def _template_login(self, prompt: str) -> str:
        return """
            <div className="flex min-h-[400px] items-center justify-center">
                <div className="w-full max-w-md space-y-8 bg-nexus-dark p-8 rounded-2xl border border-gray-800 shadow-2xl">
                    <div className="text-center">
                        <h2 className="text-3xl font-bold tracking-tight text-white">Sign in to account</h2>
                        <p className="mt-2 text-sm text-gray-400">
                            Or <a href="#" className="font-medium text-primary hover:text-blue-500">start your 14-day free trial</a>
                        </p>
                    </div>
                    <form className="mt-8 space-y-6" action="#" method="POST">
                        <div className="-space-y-px rounded-md shadow-sm opacity-100">
                            <div className="mb-4">
                                <label htmlFor="email-address" className="sr-only">Email address</label>
                                <input id="email-address" name="email" type="email" autoComplete="email" required className="relative block w-full rounded-md border-0 bg-gray-900/50 py-3 px-4 text-white ring-1 ring-inset ring-gray-700 placeholder:text-gray-500 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm sm:leading-6" placeholder="Email address" />
                            </div>
                            <div>
                                <label htmlFor="password" className="sr-only">Password</label>
                                <input id="password" name="password" type="password" autoComplete="current-password" required className="relative block w-full rounded-md border-0 bg-gray-900/50 py-3 px-4 text-white ring-1 ring-inset ring-gray-700 placeholder:text-gray-500 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm sm:leading-6" placeholder="Password" />
                            </div>
                        </div>

                        <div>
                            <button type="submit" className="group relative flex w-full justify-center rounded-md bg-primary py-3 px-3 text-sm font-semibold text-white hover:bg-blue-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 transition-all hover:shadow-[0_0_15px_rgba(59,130,246,0.5)]">
                                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-blue-300">
                                    <svg className="h-5 w-5 group-hover:text-white" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                        <path fillRule="evenodd" d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z" clipRule="evenodd" />
                                    </svg>
                                </span>
                                Sign in
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        """

    # Template: Pricing Table (New for Cycle 010)
    def _template_pricing(self, prompt: str) -> str:
        return """
            <div className="py-8 px-4 mx-auto max-w-screen-xl lg:py-16 lg:px-6">
                <div className="mx-auto max-w-screen-md text-center mb-8 lg:mb-12">
                    <h2 className="mb-4 text-4xl tracking-tight font-extrabold text-white">Designed for business teams like yours</h2>
                    <p className="mb-5 font-light text-gray-400 sm:text-xl">Here at Flowbite we focus on markets where technology, innovation, and capital can unlock long-term value and drive economic growth.</p>
                </div>
                <div className="space-y-8 lg:grid lg:grid-cols-3 sm:gap-6 xl:gap-10 lg:space-y-0">
                    {/* Starter Plan */}
                    <div className="flex flex-col p-6 mx-auto max-w-lg text-center rounded-lg border border-gray-800 shadow-xl bg-nexus-dark xl:p-8 hover:border-primary transition-colors duration-300">
                        <h3 className="mb-4 text-2xl font-semibold text-white">Starter</h3>
                        <p className="font-light text-gray-400 sm:text-lg">Best option for personal use & for your next project.</p>
                        <div className="flex justify-center items-baseline my-8">
                            <span className="mr-2 text-5xl font-extrabold text-white">$29</span>
                            <span className="text-gray-400">/month</span>
                        </div>
                        <ul role="list" className="mb-8 space-y-4 text-left text-gray-400">
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>Individual configuration</span></li>
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>No setup, or hidden fees</span></li>
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>Team size: <span className="font-semibold text-white">1 developer</span></span></li>
                        </ul>
                        <button className="text-white bg-primary hover:bg-blue-600 focus:ring-4 focus:ring-blue-900 font-medium rounded-lg text-sm px-5 py-2.5 text-center transition-all">Get started</button>
                    </div>
                    {/* Company Plan */}
                    <div className="flex flex-col p-6 mx-auto max-w-lg text-center rounded-lg border border-primary shadow-2xl bg-gray-900 xl:p-8 transform scale-105 relative">
                        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-blue-500 to-purple-600 px-4 py-1 rounded-full text-xs font-bold uppercase tracking-wide">Most Popular</div>
                        <h3 className="mb-4 text-2xl font-semibold text-white">Company</h3>
                        <p className="font-light text-gray-400 sm:text-lg">Relevant for multiple users, extended & premium support.</p>
                        <div className="flex justify-center items-baseline my-8">
                            <span className="mr-2 text-5xl font-extrabold text-white">$99</span>
                            <span className="text-gray-400">/month</span>
                        </div>
                        <ul role="list" className="mb-8 space-y-4 text-left text-gray-400">
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>Individual configuration</span></li>
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>No setup, or hidden fees</span></li>
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>Team size: <span className="font-semibold text-white">10 developers</span></span></li>
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>Premium support: <span className="font-semibold text-white">24 months</span></span></li>
                        </ul>
                        <button className="text-white bg-gradient-to-r from-primary to-purple-600 hover:bg-gradient-to-br focus:ring-4 focus:ring-purple-900 font-medium rounded-lg text-sm px-5 py-2.5 text-center transition-all shadow-lg hover:shadow-primary/50">Get started</button>
                    </div>
                    {/* Enterprise Plan */}
                    <div className="flex flex-col p-6 mx-auto max-w-lg text-center rounded-lg border border-gray-800 shadow-xl bg-nexus-dark xl:p-8 hover:border-primary transition-colors duration-300">
                        <h3 className="mb-4 text-2xl font-semibold text-white">Enterprise</h3>
                        <p className="font-light text-gray-400 sm:text-lg">Best for large scale uses and extended redistribution rights.</p>
                        <div className="flex justify-center items-baseline my-8">
                            <span className="mr-2 text-5xl font-extrabold text-white">$499</span>
                            <span className="text-gray-400">/month</span>
                        </div>
                        <ul role="list" className="mb-8 space-y-4 text-left text-gray-400">
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>Individual configuration</span></li>
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>No setup, or hidden fees</span></li>
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>Team size: <span className="font-semibold text-white">100+ developers</span></span></li>
                            <li className="flex items-center space-x-3"><span className="text-green-500">✓</span><span>Premium support: <span className="font-semibold text-white">36 months</span></span></li>
                        </ul>
                        <button className="text-white bg-primary hover:bg-blue-600 focus:ring-4 focus:ring-blue-900 font-medium rounded-lg text-sm px-5 py-2.5 text-center transition-all">Get started</button>
                    </div>
                </div>
            </div>
        """

    # Template: Hero Section (New for Cycle 010)
    def _template_hero(self, prompt: str) -> str:
        return """
            <div className="relative isolate overflow-hidden bg-nexus-darker px-6 pt-16 shadow-2xl sm:px-16 md:pt-24 lg:flex lg:gap-x-20 lg:px-24 lg:pt-0">
                <svg viewBox="0 0 1024 1024" className="absolute left-1/2 top-1/2 -z-10 h-[64rem] w-[64rem] -translate-y-1/2 [mask-image:radial-gradient(closest-side,white,transparent)] sm:left-full sm:-ml-80 lg:left-1/2 lg:ml-0 lg:-translate-x-1/2 lg:translate-y-0" aria-hidden="true">
                    <circle cx="512" cy="512" r="512" fill="url(#759c1415-0410-454c-8f7c-9a820de03641)" fillOpacity="0.7" />
                    <defs>
                        <radialGradient id="759c1415-0410-454c-8f7c-9a820de03641">
                            <stop stopColor="#3B82F6" />
                            <stop offset="1" stopColor="#A855F7" />
                        </radialGradient>
                    </defs>
                </svg>
                <div className="mx-auto max-w-md text-center lg:mx-0 lg:flex-auto lg:py-32 lg:text-left">
                    <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                        Boost your productivity.<br />Start using NEXUS today.
                    </h2>
                    <p className="mt-6 text-lg leading-8 text-gray-300">
                        Ac euismod vel sit maecenas id pellentesque eu sed consectetur. Malesuada adipiscing sagittis vel nulla.
                    </p>
                    <div className="mt-10 flex items-center justify-center gap-x-6 lg:justify-start">
                        <a href="#" className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-gray-900 shadow-sm hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">Get started</a>
                        <a href="#" className="text-sm font-semibold leading-6 text-white">Learn more <span aria-hidden="true">→</span></a>
                    </div>
                </div>
                <div className="relative mt-16 h-80 lg:mt-8">
                    <div className="absolute left-0 top-0 w-[57rem] max-w-none rounded-md bg-white/5 ring-1 ring-white/10">
                        {/* Placeholder for app screenshot */}
                        <div className="h-[400px] w-full flex items-center justify-center text-gray-400 border border-dashed border-gray-700 rounded-md">
                            [App Interface Preview]
                        </div>
                    </div>
                </div>
            </div>
        """

    async def _generate_from_llm(self, prompt: str) -> str:
        """
        Generate Component code using Async Driver.
        """
        await self._init_driver()
        
        if not self.driver:
            raise RuntimeError("LLM Driver not initialized")

        logger.info(f"Synthesizing component via Claude: '{prompt}'")
        
        # specific context construction
        context = f"""
{self.system_prompt}

# USER REQUEST
{prompt}
"""
        try:
            # Async invocation
            response = await self.driver.invoke(context)
            
            # Extract content from JSON response
            # Format: {"sender": ..., "content": "CODE HERE", ...}
            content = response.get("content", "")
            
            # Clean up Markdown code blocks if present (Driver might leave them inside JSON content)
            cleaned_content = content.replace("```tsx", "").replace("```", "").strip()
            
            return cleaned_content
            
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            raise

    async def generate_async(self, prompt: str, component_name: str = "GeneratedComponent", use_llm: bool = True) -> str:
        """
        Generates a React component file based on the prompt (Async).
        
        Args:
            prompt: User description
            component_name: Filename (without .tsx)
            use_llm: Whether to use AI (default True) or Templates
        
        Returns:
            str: Path to generated file
        """
        # 1. Validation
        if not self.validate_prompt(prompt):
            raise ValueError("Invalid prompt provided")
            
        prompt_lower = prompt.lower()
        code = ""
        
        # 2. Try LLM Generation first (if enabled)
        if use_llm:
            try:
                code = await self._generate_from_llm(prompt)
            except Exception as e:
                logger.warning(f"LLM generation failed, falling back to templates: {e}")
                # Fallthrough to templates
        
        # 3. Fallback to Templates (or if LLM disabled/failed)
        if not code:
            if "pricing" in prompt_lower:
                code = self._template_pricing(prompt)
            elif "hero" in prompt_lower:
                code = self._template_hero(prompt)
            elif "button" in prompt_lower:
                code = self._template_button(prompt)
            elif "card" in prompt_lower:
                code = self._template_card(prompt)
            elif "dashboard" in prompt_lower:
                code = self._template_dashboard(prompt)
            elif "login" in prompt_lower or "sign in" in prompt_lower:
                code = self._template_login(prompt)
            else:
                code = self._template_default(prompt)

        # 3. Wrap in Component Structure
        full_code = self._wrap_component(component_name, code)
        
        # 4. Write to File (Robust)
        try:
            file_path = os.path.join(self.output_dir, f"{component_name}.tsx")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_code)
            logger.info(f"Generated {component_name} at {file_path}")
            return file_path
        except IOError as e:
            logger.error(f"Failed to write component: {e}")
            raise

    # Sync wrapper for compatibility
    def generate(self, prompt: str, component_name: str = "GeneratedComponent", use_llm: bool = True) -> str:
        return asyncio.run(self.generate_async(prompt, component_name, use_llm))

    def _wrap_component(self, name: str, jsx: str) -> str:
        return textwrap.dedent(f"""
            import React from 'react';
            import {{ clsx }} from 'clsx';
            
            export default function {name}() {{
                return (
                    <div className="p-8 bg-nexus-darker min-h-full text-white animate-fade-in">
                        <div className="mb-6 flex items-center space-x-2 opacity-50 hover:opacity-100 transition-opacity">
                            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                            <span className="text-xs font-mono text-primary">&lt;{name} /&gt;</span>
                        </div>
                        {jsx}
                    </div>
                );
            }}
        """).strip()

    def _template_button(self, prompt: str) -> str:
        return """
            <button className="px-6 py-3 bg-primary hover:bg-blue-600 rounded-lg font-bold shadow-lg transition-all hover:scale-105 active:scale-95 text-white">
                Clicked Me!
            </button>
        """

    def _template_card(self, prompt: str) -> str:
        return """
            <div className="max-w-sm rounded-xl overflow-hidden shadow-2xl bg-nexus-dark border border-gray-700 p-6 transition-all hover:border-primary hover:shadow-primary/20">
                <div className="h-2 bg-gradient-to-r from-primary to-purple-500 mb-4 rounded-full"></div>
                <h3 className="text-2xl font-bold mb-2 text-white">Generative Card</h3>
                <p className="text-gray-400">
                    This component was generated locally by NEXUS Cycle 010.
                </p>
            </div>
        """

    def _template_dashboard(self, prompt: str) -> str:
        return """
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[1, 2, 3].map(i => (
                    <div key={i} className="bg-nexus-dark p-6 rounded-xl border border-gray-800 hover:bg-gray-800/50 transition-colors">
                        <div className="text-4xl font-bold text-primary mb-2">{i * 124}</div>
                        <div className="text-sm text-gray-500 uppercase tracking-wider">Active Agents</div>
                    </div>
                ))}
            </div>
        """

    def _template_default(self, prompt: str) -> str:
        return f"""
            <div className="border border-dashed border-gray-700 rounded-lg p-12 text-center bg-gray-900/30">
                <p className="text-xl text-gray-300 font-light">NEXUS recieved: <span className="text-primary font-mono">"{prompt}"</span></p>
                <div className="mt-4 flex justify-center">
                    <div className="h-1 w-24 bg-gradient-to-r from-transparent via-primary to-transparent opacity-50"></div>
                </div>
            </div>
        """

# CLI Entry Point for testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    prompt = sys.argv[1] if len(sys.argv) > 1 else "dashboard"
    
    # Robust path handling
    cwd = os.getcwd()
    if 'cerebro' in cwd:
         output = "src/components/generated"
    else:
         # Default to assuming running from project root
         output = "interface/ui/cerebro/src/components/generated"
         
    # Ensure dir exists
    try:
        gen = ComponentGenerator(output)
        path = gen.generate(prompt)
        print(f"Generated: {path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
