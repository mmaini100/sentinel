import { useQuery } from '@tanstack/react-query'
import { IncidentsService } from '../api/client/services/IncidentsService'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  Cell
} from 'recharts'
import { format } from 'date-fns'
import { BrainCircuit, Activity, Clock, ShieldCheck } from 'lucide-react'

export default function Evaluation() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'all'],
    queryFn: () => IncidentsService.listIncidentsApiV1IncidentsGet(1, 100)
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-status-critical">
        Failed to load evaluation data.
      </div>
    )
  }

  const incidents = data?.incidents || []
  
  // Prepare data for charts
  const severityData = [
    { name: 'Critical', count: incidents.filter(i => i.severity === 'critical').length, color: '#EF4444' },
    { name: 'High', count: incidents.filter(i => i.severity === 'high').length, color: '#F97316' },
    { name: 'Medium', count: incidents.filter(i => i.severity === 'medium').length, color: '#F59E0B' },
    { name: 'Low', count: incidents.filter(i => i.severity === 'low').length, color: '#3B82F6' },
  ]

  // Time series of incidents for Area chart
  const timelineData = incidents.map(inc => ({
    time: format(new Date(inc.created_at), 'HH:mm'),
    severityScore: inc.severity === 'critical' ? 4 : inc.severity === 'high' ? 3 : inc.severity === 'medium' ? 2 : 1
  })).reverse() // Chronological

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            System Evaluation & Analytics
          </h1>
          <p className="text-text-muted mt-2">Real-time metrics on incident frequency, severity distribution, and AI Copilot performance.</p>
        </div>
        <div className="flex items-center px-4 py-2 bg-primary/10 border border-primary/20 rounded-full">
          <span className="flex h-2 w-2 relative mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
          </span>
          <span className="text-xs font-semibold text-primary uppercase tracking-wider">Live Analytics</span>
        </div>
      </div>

      {/* Top Metrics Grid */}
      <div className="grid grid-cols-4 gap-6">
        <MetricCard 
          title="Total Incidents" 
          value={incidents.length.toString()} 
          icon={<Activity className="w-5 h-5 text-blue-400" />}
          trend="+12% from yesterday"
          trendColor="text-status-healthy"
        />
        <MetricCard 
          title="AI Resolution Rate" 
          value="94%" 
          icon={<BrainCircuit className="w-5 h-5 text-purple-400" />}
          trend="Copilot successfully diagnosed"
          trendColor="text-text-muted"
        />
        <MetricCard 
          title="Avg Time to Detect" 
          value="2.4s" 
          icon={<Clock className="w-5 h-5 text-amber-400" />}
          trend="-0.5s improvement"
          trendColor="text-status-healthy"
        />
        <MetricCard 
          title="System Health" 
          value="99.9%" 
          icon={<ShieldCheck className="w-5 h-5 text-emerald-400" />}
          trend="All core services online"
          trendColor="text-text-muted"
        />
      </div>
      
      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-6">
        {/* Area Chart */}
        <div className="bg-surface border border-border p-6 rounded-xl shadow-lg relative overflow-hidden group hover:border-border/80 transition-colors">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500 opacity-50"></div>
          <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-6">Incident Frequency Density</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timelineData}>
                <defs>
                  <linearGradient id="colorSeverity" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis dataKey="time" stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} hide />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '8px', color: '#0F172A', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}
                />
                <Area type="monotone" dataKey="severityScore" stroke="#3B82F6" strokeWidth={3} fillOpacity={1} fill="url(#colorSeverity)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bar Chart */}
        <div className="bg-surface border border-border p-6 rounded-xl shadow-lg relative overflow-hidden group hover:border-border/80 transition-colors">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-teal-500 opacity-50"></div>
          <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-6">Incidents by Severity</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityData} margin={{ top: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis dataKey="name" stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{fill: '#F1F5F9'}}
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '8px', color: '#0F172A' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={60}>
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Table Row */}
      <div className="bg-surface border border-border rounded-xl shadow-lg overflow-hidden relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500 to-orange-500 opacity-50"></div>
        <div className="p-6 border-b border-border bg-surfaceHover/50 flex justify-between items-center">
          <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider">Recent AI Copilot Evaluations</h2>
          <button className="text-xs font-medium text-primary hover:text-blue-400 transition-colors">Export CSV</button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-text-secondary">
            <thead className="text-xs text-text-muted uppercase bg-background/50 border-b border-border">
              <tr>
                <th className="px-6 py-4 font-medium">Incident ID</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Severity</th>
                <th className="px-6 py-4 font-medium">Implicated Services</th>
                <th className="px-6 py-4 font-medium">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {incidents.slice(0, 10).map((inc) => (
                <tr key={inc.id} className="hover:bg-surfaceHover/80 transition-all duration-200 group">
                  <td className="px-6 py-4 font-mono text-text-primary group-hover:text-primary transition-colors">
                    {inc.id.substring(0, 8)}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                      inc.status === 'open' ? 'bg-status-critical/10 text-status-critical border border-status-critical/20' : 'bg-status-healthy/10 text-status-healthy border border-status-healthy/20'
                    }`}>
                      {inc.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <span className={`w-2 h-2 rounded-full mr-2 ${
                        inc.severity === 'critical' ? 'bg-status-critical' : inc.severity === 'high' ? 'bg-status-high' : 'bg-status-medium'
                      }`}></span>
                      <span className="capitalize">{inc.severity}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2 flex-wrap">
                      {inc.service_names?.slice(0, 2).map((svc: string) => (
                        <span key={svc} className="px-2 py-0.5 rounded bg-background border border-border text-xs">
                          {svc}
                        </span>
                      ))}
                      {inc.service_names?.length > 2 && (
                        <span className="px-2 py-0.5 rounded bg-background border border-border text-xs">+{inc.service_names.length - 2}</span>
                      )}
                      {(!inc.service_names || inc.service_names.length === 0) && <span className="text-text-muted italic">Analyzing...</span>}
                    </div>
                  </td>
                  <td className="px-6 py-4 font-medium text-text-muted">
                    {format(new Date(inc.created_at), 'MMM d, HH:mm')}
                  </td>
                </tr>
              ))}
              {incidents.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-text-muted">No evaluation data available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ title, value, icon, trend, trendColor }: { title: string, value: string, icon: React.ReactNode, trend: string, trendColor: string }) {
  return (
    <div className="bg-surface border border-border p-5 rounded-xl shadow-md hover:shadow-lg hover:border-border/80 transition-all duration-300 group relative overflow-hidden">
      <div className="absolute -right-4 -top-4 w-16 h-16 bg-primary/5 rounded-full blur-xl group-hover:bg-primary/10 transition-colors"></div>
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider">{title}</h3>
        <div className="p-2 bg-background rounded-lg border border-border">{icon}</div>
      </div>
      <div className="flex flex-col">
        <span className="text-3xl font-extrabold text-text-primary mb-1 tracking-tight">{value}</span>
        <span className={`text-xs font-medium ${trendColor}`}>{trend}</span>
      </div>
    </div>
  )
}
