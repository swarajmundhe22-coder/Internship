/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Act1GlobalDashboard from './components/Act1GlobalDashboard';
import Act2DataInput from './components/Act2DataInput';
import Act3PredictionEngine from './components/Act3PredictionEngine';
import Act4Timeline from './components/Act4Timeline';
import Act5Blueprint from './components/Act5Blueprint';
import ErrorBoundary from './components/ErrorBoundary';
import {
  Activity,
  BarChart3,
  BookOpen,
  Bot,
  ChevronLeft,
  ChevronRight,
  CloudCheck,
  Command,
  Cpu,
  Globe,
  LayoutDashboard,
  Lock,
  LogIn,
  LogOut,
  Menu,
  Plus,
  Search,
  Shield,
  Sparkles,
  Wifi,
  X,
} from 'lucide-react';
import { Toaster } from 'sonner';
import ProjectDashboard from './components/ProjectDashboard';
import { useCommandPalette } from './useCommandPalette';
import { useLocalSimPlatform } from './useLocalSimPlatform';
import type { Act, CommandPaletteAction } from './types';

import Act0Briefing from './components/Act0Briefing';
import ComparisonView from './components/ComparisonView';
import EngineeringManual from './components/EngineeringManual';
import AIAdvisor from './components/AIAdvisor';
import ComplianceRoadmap from './components/ComplianceRoadmap';
import MaterialIntelligence from './components/MaterialIntelligence';
import PortfolioAnalytics from './components/PortfolioAnalytics';
import GeospatialRiskMap from './components/GeospatialRiskMap';
import { useRealtimeHudMetrics, type RealtimeHudMetrics } from './useRealtimeHudMetrics';

type SystemStatusProps = {
  metrics: RealtimeHudMetrics;
};

const SystemStatus = ({ metrics }: SystemStatusProps) => {

  return (
    <div className="fixed top-0 left-0 w-full z-[60] p-2 md:p-4 flex justify-between items-center pointer-events-none">
      <div className="flex items-center gap-3 md:gap-8">
        <div className="flex items-center gap-1 md:gap-2">
          <Shield className="w-2 h-2 md:w-3 md:h-3 text-accent" />
          <span className="text-[6px] md:text-[8px] font-mono font-bold uppercase tracking-widest text-white/40">{metrics.securityLabel}</span>
        </div>
        <div className="hidden sm:flex items-center gap-2">
          <Cpu className="w-3 h-3 text-accent" />
          <span className="text-[8px] font-mono font-bold uppercase tracking-widest text-white/40">{metrics.computeTflopsLabel}</span>
        </div>
        <div className="flex items-center gap-1 md:gap-2">
          <Wifi className="w-2 h-2 md:w-3 md:h-3 text-accent" />
          <span className="text-[6px] md:text-[8px] font-mono font-bold uppercase tracking-widest text-white/40">{metrics.latencyLabel}</span>
        </div>
      </div>
      <div className="flex items-center gap-3 md:gap-8">
        <div className="hidden sm:flex items-center gap-2">
          <Lock className="w-3 h-3 text-accent" />
          <span className="text-[8px] font-mono font-bold uppercase tracking-widest text-white/40">{metrics.encryptionLabel}</span>
        </div>
        <div className="text-[7px] md:text-[10px] font-mono font-bold text-white/40">
          {metrics.localClockLabel}
        </div>
      </div>
    </div>
  );
};

const CustomCursor = () => {
  const cursorRef = useRef<HTMLDivElement>(null);
  const followerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const moveCursor = (e: MouseEvent) => {
      if (cursorRef.current && followerRef.current) {
        cursorRef.current.style.transform = `translate3d(${e.clientX - 10}px, ${e.clientY - 10}px, 0)`;
        followerRef.current.style.transform = `translate3d(${e.clientX - 20}px, ${e.clientY - 20}px, 0)`;
      }
      document.documentElement.style.setProperty('--mouse-x', `${(e.clientX / window.innerWidth) * 100}%`);
      document.documentElement.style.setProperty('--mouse-y', `${(e.clientY / window.innerHeight) * 100}%`);
    };

    window.addEventListener('mousemove', moveCursor);
    return () => window.removeEventListener('mousemove', moveCursor);
  }, []);

  return (
    <>
      <div ref={cursorRef} className="custom-cursor" />
      <div ref={followerRef} className="custom-cursor-follower" />
    </>
  );
};

export default function App() {
  const realtimeHudMetrics = useRealtimeHudMetrics();

  const {
    user,
    isAuthReady,
    currentAct,
    setCurrentAct,
    simulationData,
    simulationResult,
    narrative,
    currentProject,
    isSyncing,
    showAIAdvisor,
    setShowAIAdvisor,
    allProjects,
    handleSignIn,
    handleSignOut,
    startSimulation,
    handleProjectSelect,
    openProjectComparison,
    handleSaveScenario,
    handleNewProject,
    completeSimulation,
    resetToStart,
  } = useLocalSimPlatform();

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const commandActions: CommandPaletteAction[] = useMemo(() => [
    {
      id: 'new-project',
      label: 'Start New Project',
      hint: 'Jump to ACT2 and reset draft context',
      run: handleNewProject,
    },
    {
      id: 'open-vault',
      label: 'Open Project Vault',
      hint: 'Review archived projects and linked simulations',
      run: () => setCurrentAct('ACT_DASHBOARD'),
    },
    {
      id: 'open-manual',
      label: 'Open Engineering Manual',
      hint: 'Reference measurement and compliance guidelines',
      run: () => setCurrentAct('ACT_MANUAL'),
    },
    {
      id: 'toggle-advisor',
      label: showAIAdvisor ? 'Hide AI Advisor' : 'Show AI Advisor',
      hint: 'Toggle contextual copilot panel',
      run: () => setShowAIAdvisor((prev) => !prev),
    },
    {
      id: 'risk-map',
      label: 'Open Geospatial Risk Map',
      hint: 'Inspect distributed risk overlays',
      run: () => setCurrentAct('ACT_GEOSPATIAL_MAP'),
    },
    {
      id: 'portfolio',
      label: 'Open Portfolio Analytics',
      hint: 'See aggregate asset and loss trends',
      run: () => setCurrentAct('ACT_PORTFOLIO_ANALYTICS'),
    },
  ], [handleNewProject, setCurrentAct, setShowAIAdvisor, showAIAdvisor]);

  const {
    isOpen: isCommandPaletteOpen,
    setIsOpen: setIsCommandPaletteOpen,
    query: commandQuery,
    setQuery: setCommandQuery,
    inputRef: commandInputRef,
    filteredActions: filteredCommandActions,
    runAction: runCommand,
  } = useCommandPalette(commandActions);

  const nextAct = () => {
    const acts: Act[] = ['ACT0', 'ACT1', 'ACT_DASHBOARD', 'ACT2', 'ACT3', 'ACT4', 'ACT5'];
    const currentIndex = acts.indexOf(currentAct);
    if (currentIndex < acts.length - 1) {
      setCurrentAct(acts[currentIndex + 1]);
    }
  };

  const prevAct = () => {
    const acts: Act[] = ['ACT0', 'ACT1', 'ACT_DASHBOARD', 'ACT2', 'ACT3', 'ACT4', 'ACT5'];
    const currentIndex = acts.indexOf(currentAct);
    if (currentIndex > 0) {
      setCurrentAct(acts[currentIndex - 1]);
    }
  };

  if (!isAuthReady) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="local-simulated-app relative min-h-screen bg-black text-white selection:bg-accent selection:text-bg overflow-hidden">
        <SystemStatus metrics={realtimeHudMetrics} />
        <CustomCursor />
        <div className="fixed inset-0 atmosphere-gradient pointer-events-none z-0" />
        <div className="noise-overlay" />
        
        {/* Navigation Overlay */}
        <nav className="fixed top-0 left-0 w-full z-50 p-2 md:p-6 flex justify-between items-center pointer-events-none mt-6 md:mt-0">
          <div className="flex items-center gap-2 md:gap-4 pointer-events-auto">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 md:p-3 border border-white/10 bg-black/50 backdrop-blur-xl rounded-full text-white hover:border-accent transition-all"
            >
              {isMobileMenuOpen ? <X className="w-4 h-4 md:w-5 md:h-5" /> : <Menu className="w-4 h-4 md:w-5 md:h-5" />}
            </button>
            
            <button
              onClick={() => setCurrentAct('ACT_MANUAL')}
              className="hidden md:flex items-center gap-2 px-4 py-2 border border-white/10 bg-black/50 backdrop-blur-xl rounded-full text-[10px] font-mono uppercase tracking-widest hover:border-accent transition-all"
            >
              <BookOpen className="w-4 h-4 text-accent" /> Manual
            </button>

            <button
              onClick={() => setIsCommandPaletteOpen(true)}
              className="hidden lg:flex items-center gap-2 px-4 py-2 border border-white/10 bg-black/50 backdrop-blur-xl rounded-full text-[10px] font-mono uppercase tracking-widest hover:border-accent transition-all"
            >
              <Command className="w-4 h-4 text-accent" /> Cmd
            </button>
            
            {user ? (
              <div className="flex items-center gap-2 md:gap-3 p-1.5 md:p-2 border border-white/10 bg-black/50 backdrop-blur-xl rounded-full">
                <div className="w-6 h-6 md:w-8 md:h-8 rounded-full border border-white/20 bg-accent/15 flex items-center justify-center text-[9px] md:text-[10px] font-black uppercase">
                  {user.displayName.charAt(0)}
                </div>
                <span className="text-[8px] md:text-[10px] font-mono uppercase tracking-widest hidden sm:block">{user.displayName?.split(' ')[0]}</span>
                <button onClick={handleSignOut} className="p-1.5 md:p-2 hover:text-orange-500 transition-colors">
                  <LogOut className="w-3 h-3 md:w-4 md:h-4" />
                </button>
                <div className="w-px h-4 bg-white/10 mx-0.5 md:mx-1" />
                <div className="flex items-center gap-1 md:gap-2 px-1 md:px-2">
                  {isSyncing ? (
                    <div className="w-2 h-2 md:w-3 md:h-3 border border-accent border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <CloudCheck className="w-2 h-2 md:w-3 md:h-3 text-accent" />
                  )}
                  <span className="text-[6px] md:text-[8px] font-mono uppercase tracking-widest text-white/40 hidden xs:block">
                    {isSyncing ? 'Syncing' : 'Synced'}
                  </span>
                </div>
              </div>
            ) : (
              <button
                onClick={handleSignIn}
                className="flex items-center gap-2 px-3 md:px-4 py-1.5 md:py-2 border border-white/10 bg-black/50 backdrop-blur-xl rounded-full text-[8px] md:text-[10px] font-mono uppercase tracking-widest hover:border-orange-500 transition-all pointer-events-auto"
              >
                <LogIn className="w-3 h-3 md:w-4 md:h-4" /> Sign In
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 md:gap-4 pointer-events-auto">
            {simulationData && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowAIAdvisor(!showAIAdvisor)}
                className={`p-2.5 md:p-3 rounded-full border transition-all ${showAIAdvisor ? 'bg-accent text-bg border-accent shadow-2xl shadow-accent/40' : 'bg-white/5 border-white/10 text-white/40 hover:text-accent hover:border-accent/40'}`}
              >
                <Bot className="w-4 h-4 md:w-5 md:h-5" />
              </motion.button>
            )}
            <div className="hidden md:flex items-center gap-2">
              {['ACT0', 'ACT1', 'ACT_DASHBOARD', 'ACT2', 'ACT3', 'ACT4', 'ACT5', 'ACT_MANUAL'].map((act, i) => (
                <div
                  key={act}
                  className={`w-1.5 h-1.5 rounded-full transition-all duration-500 ${
                    currentAct === act ? 'bg-orange-500 scale-150 shadow-[0_0_10px_rgba(255,78,0,0.8)]' : 'bg-white/20'
                  }`}
                />
              ))}
            </div>
          </div>
        </nav>

        {/* Mobile Menu Overlay */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, x: -100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              className="fixed inset-0 z-[60] bg-black/95 backdrop-blur-2xl p-8 flex flex-col justify-center gap-8"
            >
              <button
                onClick={() => setIsMobileMenuOpen(false)}
                className="absolute top-8 right-8 p-4 border border-white/10 rounded-full text-white"
              >
                <X className="w-6 h-6" />
              </button>
              
              <div className="space-y-4">
                <p className="text-[10px] font-mono uppercase tracking-[0.5em] text-white/40">Navigation</p>
                <div className="flex flex-col gap-4">
                  {[
                    { id: 'ACT_DASHBOARD', label: 'Project Vault', icon: LayoutDashboard },
                    { id: 'ACT_MANUAL', label: 'Engineering Manual', icon: BookOpen },
                    { id: 'ACT_GEOSPATIAL_MAP', label: 'Risk Map', icon: Globe },
                    { id: 'ACT_PORTFOLIO_ANALYTICS', label: 'Analytics', icon: BarChart3 },
                  ].map((item) => (
                    <button
                      key={item.id}
                      onClick={() => {
                        setCurrentAct(item.id as Act);
                        setIsMobileMenuOpen(false);
                      }}
                      className={`flex items-center gap-4 p-6 border rounded-2xl transition-all ${
                        currentAct === item.id ? 'bg-accent text-bg border-accent' : 'bg-white/5 border-white/10 text-white'
                      }`}
                    >
                      <item.icon className="w-6 h-6" />
                      <span className="text-xl font-display font-black uppercase tracking-tight">{item.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Act Controls */}
        <div className="fixed bottom-4 right-4 md:bottom-8 md:right-8 z-50 flex gap-2 md:gap-4">
          {currentAct !== 'ACT0' && currentAct !== 'ACT1' && currentAct !== 'ACT3' && currentAct !== 'ACT_DASHBOARD' && (
            <button
              onClick={prevAct}
              className="p-3 md:p-4 border border-white/10 bg-black/50 backdrop-blur-xl rounded-full hover:border-orange-500 transition-all"
            >
              <ChevronLeft className="w-5 h-5 md:w-6 md:h-6" />
            </button>
          )}
          {currentAct === 'ACT1' && (
            <button
              onClick={nextAct}
              className="group flex items-center gap-2 md:gap-3 px-6 md:px-8 py-3 md:py-4 bg-orange-500 text-white font-black uppercase tracking-[0.2em] md:tracking-[0.4em] rounded-full hover:bg-orange-600 transition-all shadow-lg shadow-orange-500/20 text-xs md:text-base"
            >
              Enter Platform <ChevronRight className="w-4 h-4 md:w-5 md:h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          )}
          {currentAct === 'ACT_DASHBOARD' && (
            <button
              onClick={handleNewProject}
              className="group flex items-center gap-2 md:gap-3 px-6 md:px-8 py-3 md:py-4 bg-orange-500 text-white font-black uppercase tracking-[0.2em] md:tracking-[0.4em] rounded-full hover:bg-orange-600 transition-all shadow-lg shadow-orange-500/20 text-xs md:text-base"
            >
              New Project <Plus className="w-4 h-4 md:w-5 md:h-5 group-hover:rotate-90 transition-transform" />
            </button>
          )}
        </div>

        <div className="fixed bottom-4 left-4 md:bottom-8 md:left-8 z-50 hidden md:flex items-center gap-2">
          <button
            onClick={() => setIsCommandPaletteOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 bg-black/60 text-[10px] font-mono uppercase tracking-widest hover:border-accent transition-all"
          >
            <Search className="w-3.5 h-3.5 text-accent" /> Quick Actions
          </button>
          <button
            onClick={() => setCurrentAct('ACT_MATERIAL_INTELLIGENCE')}
            className="p-3 rounded-full border border-white/10 bg-black/60 text-white/70 hover:text-accent hover:border-accent transition-all"
            title="Material Intelligence"
          >
            <Sparkles className="w-4 h-4" />
          </button>
          <button
            onClick={() => setCurrentAct('ACT_PORTFOLIO_ANALYTICS')}
            className="p-3 rounded-full border border-white/10 bg-black/60 text-white/70 hover:text-accent hover:border-accent transition-all"
            title="Portfolio Analytics"
          >
            <Activity className="w-4 h-4" />
          </button>
        </div>

        {/* Acts */}
        <main className="w-full h-screen overflow-hidden relative z-10">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentAct}
              initial={{ opacity: 0, scale: 1.1, filter: 'blur(20px)' }}
              animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
              exit={{ opacity: 0, scale: 0.9, filter: 'blur(20px)' }}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
              className="w-full h-full"
            >
              {currentAct === 'ACT0' && <Act0Briefing onStart={() => setCurrentAct('ACT1')} />}
              {currentAct === 'ACT1' && <Act1GlobalDashboard metrics={realtimeHudMetrics} />}
              {currentAct === 'ACT_DASHBOARD' && user && (
                <ProjectDashboard 
                  user={user} 
                  projects={allProjects}
                  onSelect={handleProjectSelect} 
                  onNew={handleNewProject} 
                  onOpenManual={() => setCurrentAct('ACT_MANUAL')} 
                  onCompare={openProjectComparison}
                  onOpenCompliance={() => setCurrentAct('ACT_COMPLIANCE_ROADMAP')}
                  onOpenMaterials={() => setCurrentAct('ACT_MATERIAL_INTELLIGENCE')}
                  onOpenPortfolio={() => setCurrentAct('ACT_PORTFOLIO_ANALYTICS')}
                  onOpenMap={() => setCurrentAct('ACT_GEOSPATIAL_MAP')}
                />
              )}
              {currentAct === 'ACT_DASHBOARD' && !user && (
                <div className="w-full h-full flex items-center justify-center p-6">
                  <div className="max-w-2xl w-full glass border border-white/10 p-8 md:p-12 text-center space-y-8">
                    <div className="space-y-3">
                      <p className="text-[10px] font-mono uppercase tracking-[0.35em] text-accent">Project Vault Access</p>
                      <h2 className="text-3xl md:text-5xl font-display font-black uppercase tracking-tight text-white">Authenticate or Continue Offline</h2>
                      <p className="text-sm text-white/55 leading-relaxed">
                        Sign in to sync projects, attach simulations to your backend workspace, and unlock governed copilot guidance.
                        You can still run local simulations without account sync.
                      </p>
                      <p className="text-xs text-amber-300/85 leading-relaxed">
                        Notice: Continue Offline runs in local demo mode. Live reports, analytics graphs, and project vault history require sign in.
                      </p>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                      <button
                        onClick={handleSignIn}
                        className="px-6 py-3 bg-accent text-bg font-display font-black uppercase tracking-widest text-xs rounded-xl"
                      >
                        Sign In
                      </button>
                      <button
                        onClick={handleNewProject}
                        className="px-6 py-3 border border-white/15 text-white font-display font-black uppercase tracking-widest text-xs rounded-xl hover:border-accent transition-all"
                      >
                        Continue Offline
                      </button>
                    </div>
                  </div>
                </div>
              )}
              {currentAct === 'ACT2' && <Act2DataInput onSimulate={startSimulation} initialData={simulationData} />}
              {currentAct === 'ACT3' && <Act3PredictionEngine data={simulationData} result={simulationResult} onComplete={completeSimulation} />}
              {currentAct === 'ACT4' && <Act4Timeline result={simulationResult} narrative={narrative} onNext={() => setCurrentAct('ACT5')} />}
              {currentAct === 'ACT5' && <Act5Blueprint result={simulationResult} onReset={resetToStart} onSaveScenario={handleSaveScenario} />}
              {currentAct === 'ACT_MANUAL' && <EngineeringManual onBack={() => setCurrentAct('ACT2')} />}
              {currentAct === 'ACT_COMPARISON' && <ComparisonView scenarios={currentProject?.scenarios || []} onBack={() => setCurrentAct('ACT_DASHBOARD')} />}
              {currentAct === 'ACT_COMPLIANCE_ROADMAP' && <ComplianceRoadmap onBack={() => setCurrentAct('ACT_DASHBOARD')} />}
              {currentAct === 'ACT_MATERIAL_INTELLIGENCE' && <MaterialIntelligence onBack={() => setCurrentAct('ACT_DASHBOARD')} />}
              {currentAct === 'ACT_PORTFOLIO_ANALYTICS' && <PortfolioAnalytics projects={allProjects} onBack={() => setCurrentAct('ACT_DASHBOARD')} />}
              {currentAct === 'ACT_GEOSPATIAL_MAP' && <GeospatialRiskMap onBack={() => setCurrentAct('ACT_DASHBOARD')} />}
            </motion.div>
          </AnimatePresence>
        </main>

        <AnimatePresence>
          {showAIAdvisor && simulationData && (
            <AIAdvisor 
              simulationData={simulationData} 
              simulationResult={simulationResult} 
              onClose={() => setShowAIAdvisor(false)} 
            />
          )}
        </AnimatePresence>

        <AnimatePresence>
          {isCommandPaletteOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-[90] bg-black/70 backdrop-blur-lg p-4 md:p-8"
              onClick={() => setIsCommandPaletteOpen(false)}
            >
              <motion.div
                initial={{ opacity: 0, y: 20, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 20, scale: 0.98 }}
                transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                onClick={(event) => event.stopPropagation()}
                className="mx-auto mt-[8vh] w-full max-w-2xl rounded-2xl border border-white/10 bg-black/70 shadow-[0_30px_80px_rgba(0,0,0,0.55)]"
              >
                <div className="flex items-center gap-3 border-b border-white/10 p-4 md:p-5">
                  <Search className="w-4 h-4 text-accent" />
                  <input
                    ref={commandInputRef}
                    value={commandQuery}
                    onChange={(event) => setCommandQuery(event.target.value)}
                    placeholder="Search commands (Ctrl/Cmd+K)..."
                    className="w-full bg-transparent text-sm text-white outline-none placeholder:text-white/35"
                  />
                  <button
                    onClick={() => setIsCommandPaletteOpen(false)}
                    className="p-2 rounded-full border border-white/10 text-white/55 hover:text-white hover:border-accent transition-all"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div className="max-h-[58vh] overflow-y-auto custom-scrollbar p-2">
                  {filteredCommandActions.length === 0 ? (
                    <p className="p-4 text-xs text-white/45">No matching command. Try a broader term.</p>
                  ) : (
                    filteredCommandActions.map((action) => (
                      <button
                        key={action.id}
                        onClick={() => runCommand(action)}
                        className="w-full rounded-xl border border-transparent px-4 py-3 text-left hover:border-accent/40 hover:bg-white/5 transition-all"
                      >
                        <p className="text-sm font-semibold text-white">{action.label}</p>
                        <p className="mt-1 text-[11px] text-white/45 uppercase tracking-wide">{action.hint}</p>
                      </button>
                    ))
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        <Toaster position="bottom-left" theme="dark" />

        {/* Global Cinematic Overlay */}
        <div className="fixed inset-0 pointer-events-none border-[40px] border-black/20 z-40" />
        <div className="fixed inset-0 pointer-events-none bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03] z-50" />
      </div>
    </ErrorBoundary>
  );
}


