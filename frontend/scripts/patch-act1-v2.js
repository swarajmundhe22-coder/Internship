const fs = require('fs');
const file = 'c:/Users/s22td/OneDrive/Documents/The On Lookers/frontend/components/outsource/local-simulated/components/Act1GlobalDashboard.tsx';
let src = fs.readFileSync(file, 'utf8');
const start = src.indexOf('const Act1GlobalDashboard = ({ metrics }: Act1GlobalDashboardProps) => {');
const end = src.indexOf('  return (', start);

const injection = `const Act1GlobalDashboard = ({ metrics }: Act1GlobalDashboardProps) => {
  const [corrosionCost, setCorrosionCost] = React.useState(0);
  const [seismicData, setSeismicData] = React.useState([...Array(20)].map(() => 10));
  const [systemStats, setSystemStats] = React.useState({ cpuCores: 0, memTotal: 0, memUsed: 0, memPercent: 0, cpuUsage: 0, activeConns: 0 });
  const [threatData, setThreatData] = React.useState({ count: 12, level: 'LOADING...' });

  React.useEffect(() => {
    const startOfYear = new Date(new Date().getFullYear(), 0, 1).getTime();
    const updateCost = () => {
      const now = Date.now();
      const secondsSinceYearStart = (now - startOfYear) / 1000;
      setCorrosionCost(secondsSinceYearStart * 79274.48);
    };
    const timer = setInterval(updateCost, 1000);
    updateCost();

    const fetchSeismic = async () => {
      try {
        const res = await fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson');
        const data = await res.json();
        let heights = [];
        if (data && data.features) {
          heights = data.features.slice(0, 20).map((f) => Math.max(2, (f.properties?.mag || 1) * 5));
        }
        if (heights.length < 20) {
          while (heights.length < 20) heights.push(2);
        }
        setSeismicData(heights);
      } catch (err) {}
    };

    const fetchSystem = async () => {
      const localCores = typeof navigator !== 'undefined' ? navigator.hardwareConcurrency || 4 : 4;
      try {
        const res = await fetch('http://localhost:8000/ops/metrics/live?api_key=SIMULATED_KEY_123');
        if (res.ok) {
          const s = await res.json();
          setSystemStats({
            cpuCores: s.cpu?.cores || localCores,
            memTotal: s.memory?.total_gb || 0,
            memUsed: s.memory?.used_gb || 0,
            memPercent: s.memory?.usage_percent || 0,
            cpuUsage: s.cpu?.usage_percent || 0,
            activeConns: s.network?.active_connections || 0
          });
        }
      } catch (err) {
        setSystemStats(prev => ({ ...prev, cpuCores: localCores }));
      }
    };

    const fetchThreats = async () => {
      try {
        const res = await fetch('https://urlhaus-api.abuse.ch/v1/urls/recent/', { method: 'GET'});
        if (res.ok) {
          const data = await res.json();
          const count = data.urls ? data.urls.length : 12;
          setThreatData({ count, level: count > 50 ? 'CRITICAL' : 'HIGH' });
        } else {
          setThreatData({ count: 12, level: 'HIGH' });
        }
      } catch (err) {
        setThreatData({ count: 12, level: 'HIGH' });
      }
    };

    fetchSeismic();
    fetchSystem();
    fetchThreats();

    const intS = setInterval(fetchSeismic, 5 * 60 * 1000);
    const intH = setInterval(fetchSystem, 3000);
    const intT = setInterval(fetchThreats, 10 * 60 * 1000);

    return () => {
      clearInterval(timer);
      clearInterval(intS);
      clearInterval(intH);
      clearInterval(intT);
    };
  }, []);

  const stats = [
    { label: 'Est. Global Loss (YTD)', value: \`$\${(corrosionCost / 1e9).toFixed(2)}B\`, icon: GlobeIcon, color: 'text-accent' },
    { label: 'Annual GDP Impact', value: '3.4%', icon: Shield, color: 'text-blue-400' },
    { label: 'Network Connections', value: systemStats.activeConns.toLocaleString(), icon: Cpu, color: 'text-accent' },
    { label: 'Threat Traces', value: threatData.count.toLocaleString(), icon: Activity, color: 'text-accent' },
  ];\n\n`;

src = src.substring(0, start) + injection + src.substring(end);
fs.writeFileSync(file, src);
console.log('Fixed runtime ReferenceError.');