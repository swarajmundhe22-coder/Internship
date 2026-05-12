const fs = require('fs');
const file = 'c:/Users/s22td/OneDrive/Documents/The On Lookers/frontend/components/outsource/local-simulated/components/Act1GlobalDashboard.tsx';
let source = fs.readFileSync(file, 'utf8');

// Replace FUIOverlay Props
source = source.replace('type FUIOverlayProps = {', `type FUIOverlayProps = {
  seismicData: number[];
  systemStats: { cpuCores: number; memTotal: number; memUsed: number; memPercent: number; cpuUsage: number; activeConns: number };
  threatData: { count: number; level: string };`);
source = source.replace('const FUIOverlay = ({ metrics }: FUIOverlayProps) => {', 'const FUIOverlay = ({ metrics, seismicData, systemStats, threatData }: FUIOverlayProps) => {');

// Replace Seismic Array mapping
const seismicRegex = /\{\[\.\.\.Array\(20\)\]\.map\(\(_, i\) => \([\s\S]*?className=\"flex-1 bg-accent\/40\"\s*\/>\s*\)\)\}/g;
source = source.replace(seismicRegex, `{seismicData.slice(0, 20).map((val, i) => (
                  <motion.div
                    key={i}
                    animate={{ height: [val * 0.8, val, val * 0.9] }}
                    transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.05 }}
                    className="flex-1 bg-accent/40"
                    style={{ minHeight: '4px', height: \`\${val * 10}px\` }}
                  />
                ))}`);

// Replace Active Nodes static values
source = source.replace(
  '<div className="text-[8px] md:text-[9px] text-white/40 uppercase tracking-widest">Active Nodes</div>',
  '<div className="text-[8px] md:text-[9px] text-white/40 uppercase tracking-widest">Active Nodes (Threads)</div>'
);
source = source.replace(
  '<div className="text-xl md:text-2xl font-display font-bold text-white">1,248</div>',
  '<div className="text-xl md:text-2xl font-display font-bold text-white">{systemStats.cpuCores}</div>'
);

// Replace Threat Detection values
source = source.replace(
  '<span className="text-sm md:text-base font-mono font-bold text-red-500">12</span>',
  '<span className="text-sm md:text-base font-mono font-bold text-red-500">{threatData.count}</span>'
);
source = source.replace(
  '<span className="text-sm md:text-base font-mono font-bold text-orange-500">HIGH</span>',
  '<span className={`text-sm md:text-base font-mono font-bold ${threatData.level === "CRITICAL" ? "text-red-500" : threatData.level === "HIGH" ? "text-orange-500" : "text-accent"}`}>{threatData.level}</span>'
);

// Replace Compute Load static value -> CPU usage block and RAM
source = source.replace(
  '<div className="text-[8px] md:text-[9px] text-white/40 uppercase tracking-widest">Compute Load</div>',
  '<div className="text-[8px] md:text-[9px] text-white/40 uppercase tracking-widest">Compute Load & RAM</div>'
);
source = source.replace(
  '<div className="text-xl md:text-2xl font-display font-bold text-white">{metrics.computeLoadLabel}</div>',
  `<div className="text-xl md:text-2xl font-display font-bold text-white">CPU {systemStats.cpuUsage}%</div>
   <div className="text-xs font-mono text-white/60 mt-1">RAM {systemStats.memUsed}G / {systemStats.memTotal}G ({systemStats.memPercent}%)</div>`
);

// Now patch Act1GlobalDashboard to hold the state and pass it to FUIOverlay and stats

const act1Imports = `import React, { useRef, useMemo, useEffect, useState } from 'react';`;
source = source.replace(`import React, { useRef, useMemo, useEffect } from 'react';`, act1Imports);

// Fix FUIOverlay invocation
const act1Tag = `<FUIOverlay metrics={metrics} />`;
source = source.replace(act1Tag, `<FUIOverlay metrics={metrics} seismicData={seismicData} systemStats={systemStats} threatData={threatData} />`);

fs.writeFileSync(file, source);
console.log('FUIOverlay patching completed.');