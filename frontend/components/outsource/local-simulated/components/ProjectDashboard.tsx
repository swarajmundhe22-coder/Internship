import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Folder, Trash2, Play, Plus, Clock, Database, Globe, Search, Filter, BookOpen, BarChart3, ShieldAlert } from 'lucide-react';
import { toast } from 'sonner';

interface Project {
  id: string;
  name: string;
  parameters: any;
  createdAt?: string;
  updatedAt?: string;
  scenarios?: any[];
}

interface LocalSimUser {
  uid: string;
  email: string;
  displayName: string;
  role: string;
}

interface Props {
  user: LocalSimUser;
  projects: Project[];
  onSelect: (project: Project) => void;
  onNew: () => void;
  onOpenManual: () => void;
  onCompare?: (project: Project) => void;
  onOpenCompliance?: () => void;
  onOpenMaterials?: () => void;
  onOpenPortfolio?: () => void;
  onOpenMap?: () => void;
  onDelete?: (projectId: string) => Promise<void> | void;
}

const ProjectDashboard = ({ user, projects, onSelect, onNew, onOpenManual, onCompare, onOpenCompliance, onOpenMaterials, onOpenPortfolio, onOpenMap, onDelete }: Props) => {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All');

  const filteredProjects = projects.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) || 
                         (p.parameters?.structure || '').toLowerCase().includes(search.toLowerCase()) ||
                         (p.parameters?.material || '').toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === 'All' || p.parameters?.structure === filter;
    return matchesSearch && matchesFilter;
  });

  const structures = ['All', ...new Set(projects.map(p => p.parameters?.structure).filter(Boolean))];

  const formatDate = (value?: string) => {
    if (!value) {
      return 'No timestamp';
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return 'Invalid date';
    }
    return parsed.toLocaleDateString();
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this project?")) return;
    
    try {
      if (!onDelete) {
        toast.info('Project deletion is not available in this mode');
        return;
      }
      await onDelete(id);
      toast.success("Project deleted");
    } catch (error) {
      console.error(error);
      toast.error("Failed to delete project");
    }
  };

  return (
    <div className="w-full h-full flex flex-col p-6 md:p-12 overflow-y-auto custom-scrollbar">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-12">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <Folder className="w-6 h-6 md:w-8 md:h-8 text-accent" />
            <h2 className="text-3xl md:text-5xl font-display font-black uppercase tracking-tighter text-white">Project Vault</h2>
          </div>
          <p className="text-[8px] md:text-[10px] font-sans uppercase tracking-[0.3em] md:tracking-[0.5em] text-white/40">Infrastructure Asset Management System</p>
          <p className="text-[8px] md:text-[10px] font-mono uppercase tracking-widest text-accent/80">Operator: {user.email}</p>
        </div>
        
        <div className="flex flex-wrap gap-2 md:gap-4 w-full md:w-auto">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onOpenManual}
            className="flex-1 md:flex-none px-3 md:px-8 py-2 md:py-4 border border-white/10 bg-black/50 backdrop-blur-xl text-white font-display font-black uppercase tracking-widest text-[8px] md:text-xs rounded-lg md:rounded-xl flex items-center justify-center gap-1 md:gap-2 hover:border-accent transition-all"
          >
            <BookOpen className="w-3 h-3 md:w-4 md:h-4 text-accent" /> <span className="hidden sm:inline">Engineering</span> Manual
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onNew}
            className="flex-1 md:flex-none px-3 md:px-8 py-2 md:py-4 bg-accent text-bg font-display font-black uppercase tracking-widest text-[8px] md:text-xs rounded-lg md:rounded-xl flex items-center justify-center gap-1 md:gap-2 shadow-2xl shadow-accent/20"
          >
            <Plus className="w-3 h-3 md:w-4 md:h-4" /> New <span className="hidden sm:inline">Asset</span> Analysis
          </motion.button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 md:gap-4 mb-8 md:mb-12">
        {[
          { label: 'Compliance Roadmap', icon: ShieldAlert, onClick: onOpenCompliance, color: 'text-blue-400' },
          { label: 'Material Intelligence', icon: Database, onClick: onOpenMaterials, color: 'text-purple-400' },
          { label: 'Portfolio Analytics', icon: BarChart3, onClick: onOpenPortfolio, color: 'text-emerald-400' },
          { label: 'Geospatial Risk Map', icon: Globe, onClick: onOpenMap, color: 'text-amber-400' },
        ].map((item) => (
          <motion.button
            key={item.label}
            whileHover={{ y: -5, backgroundColor: 'rgba(255,255,255,0.05)' }}
            onClick={item.onClick}
            disabled={!item.onClick}
            className="glass p-3 md:p-6 border border-white/10 rounded-xl md:rounded-2xl flex flex-col items-center text-center gap-2 md:gap-4 group transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <div className={`p-2 md:p-3 rounded-lg md:rounded-xl bg-white/5 group-hover:bg-white/10 transition-colors ${item.color}`}>
              <item.icon className="w-4 h-4 md:w-6 md:h-6" />
            </div>
            <span className="text-[7px] md:text-[10px] font-display font-black uppercase tracking-widest text-white/60 group-hover:text-white">
              {item.label}
            </span>
          </motion.button>
        ))}
      </div>

      <div className="flex flex-col md:flex-row gap-3 md:gap-4 mb-8">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
          <input 
            type="text"
            placeholder="Search assets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-3 md:py-4 bg-white/5 border border-white/10 rounded-lg md:rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all text-xs md:text-base"
          />
        </div>
        <div className="relative min-w-full md:min-w-[200px]">
          <Filter className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full pl-12 pr-8 py-3 md:py-4 bg-white/5 border border-white/10 rounded-lg md:rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all appearance-none cursor-pointer text-xs md:text-base"
          >
            {structures.map(s => (
              <option key={s} value={s} className="bg-bg">{s}</option>
            ))}
          </select>
        </div>
      </div>

      {filteredProjects.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center space-y-6 opacity-40">
          <Database className="w-16 h-16" />
          <div className="space-y-2">
            <h3 className="text-xl font-display font-bold uppercase tracking-widest">No Assets Found</h3>
            <p className="text-xs uppercase tracking-widest">Try adjusting your search or filter</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          <AnimatePresence mode="popLayout">
            {filteredProjects.map((project, i) => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: i * 0.05 }}
                onClick={() => onSelect(project)}
                className="glass p-6 md:p-8 rounded-2xl space-y-4 md:space-y-6 group cursor-pointer hover:border-accent/40 transition-all relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-3 md:p-4 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                  {(project as any).scenarios?.length > 0 && (
                    <button 
                      onClick={(e) => { e.stopPropagation(); onCompare?.(project); }}
                      className="p-2 hover:text-accent transition-colors"
                      title="Compare Scenarios"
                    >
                      <BarChart3 className="w-4 h-4" />
                    </button>
                  )}
                  {onDelete && (
                    <button 
                      onClick={(e) => handleDelete(e, project.id)}
                      className="p-2 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>

                <div className="space-y-4">
                  <div className="p-3 bg-white/5 rounded-lg w-fit group-hover:bg-accent/10 transition-colors">
                    <Globe className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <h3 className="text-lg font-display font-bold text-white uppercase tracking-tight truncate">{project.name}</h3>
                    <p className="text-[10px] text-white/40 uppercase tracking-widest mt-1">
                      {project.parameters?.material || 'Unknown Material'}  |  {project.parameters?.structure || 'Unknown Structure'}
                    </p>
                  </div>
                </div>

                <div className="pt-6 border-t border-white/5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-[9px] font-display font-bold uppercase tracking-widest text-white/30">
                    <Clock className="w-3 h-3" />
                    {formatDate(project.updatedAt || project.createdAt)}
                  </div>
                  <div className="flex items-center gap-2 text-accent opacity-0 group-hover:opacity-100 transition-all translate-x-2 group-hover:translate-x-0">
                    <span className="text-[9px] font-display font-bold uppercase tracking-widest">Resume</span>
                    <Play className="w-3 h-3 fill-current" />
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default ProjectDashboard;

