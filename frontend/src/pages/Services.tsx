import { useQuery } from '@tanstack/react-query'
import { ServicesService } from '../api/client/services/ServicesService'
import { IncidentsService } from '../api/client/services/IncidentsService'
import ReactFlow, { 
  Background, 
  Controls, 
  Node, 
  Edge,
  MarkerType
} from 'reactflow'
import 'reactflow/dist/style.css'

export default function Services() {
  const { data: servicesData, isLoading: loadingServices, error: servicesError } = useQuery({
    queryKey: ['services'],
    queryFn: () => ServicesService.listServicesApiV1ServicesGet()
  })

  // Poll for incidents to keep the graph dynamic and real-time
  const { data: incidentsData } = useQuery({
    queryKey: ['incidents', 'all'],
    queryFn: () => IncidentsService.listIncidentsApiV1IncidentsGet(1, 100),
    refetchInterval: 2000
  })

  if (loadingServices) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (servicesError) {
    return (
      <div className="flex items-center justify-center h-full text-status-critical">
        Failed to load services.
      </div>
    )
  }

  const services = servicesData?.services || []
  const activeIncidents = incidentsData?.incidents?.filter(i => i.status === 'open') || []

  // Determine if a service is currently degraded
  const isServiceDegraded = (serviceName: string) => {
    return activeIncidents.some(inc => (inc.service_names || []).includes(serviceName))
  }

  // Simple layout engine: put services in a circle or simple grid
  const nodes: Node[] = []
  const edges: Edge[] = []
  
  const radius = 250
  const centerX = 400
  const centerY = 300
  
  services.forEach((service, i) => {
    const angle = (i / services.length) * 2 * Math.PI
    const x = centerX + radius * Math.cos(angle)
    const y = centerY + radius * Math.sin(angle)
    
    const isDegraded = isServiceDegraded(service.name)
    const statusText = isDegraded ? 'Critical' : 'Healthy'
    
    const badgeClass = isDegraded 
      ? 'bg-status-critical/20 text-status-critical border-status-critical/50'
      : 'bg-status-healthy/10 text-status-healthy border-status-healthy/20'
      
    const nodeBorder = isDegraded ? '#EF4444' : '#E2E8F0'
    const nodeGlow = isDegraded ? '0 0 15px rgba(239, 68, 68, 0.4)' : 'none'
    
    nodes.push({
      id: service.id,
      position: { x, y },
      data: { 
        label: (
          <div className="p-3 flex flex-col items-center justify-center">
            <span className="font-bold text-text-primary mb-2 tracking-wide">{service.name}</span>
            <span className={`text-xs px-2.5 py-0.5 border rounded-full font-medium ${badgeClass}`}>
              {statusText}
            </span>
          </div>
        )
      },
      style: {
        background: '#FFFFFF',
        border: `1px solid ${nodeBorder}`,
        boxShadow: nodeGlow,
        borderRadius: '12px',
        color: '#0F172A',
        width: 170,
      }
    });

    (service.dependencies || []).forEach((dep: any) => {
      // Find the target service to check its status for edge coloring
      const targetService = services.find(s => s.id === dep.depends_on_service_id)
      const isTargetDegraded = targetService && isServiceDegraded(targetService.name)
      
      const edgeColor = isDegraded || isTargetDegraded ? '#EF4444' : '#94A3B8'
      
      edges.push({
        id: `e-${service.id}-${dep.depends_on_service_id}`,
        source: service.id,
        target: dep.depends_on_service_id,
        animated: isDegraded || isTargetDegraded,
        style: { stroke: edgeColor, strokeWidth: isDegraded || isTargetDegraded ? 2 : 1 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edgeColor,
        },
      })
    })
  })

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col animate-in fade-in duration-500 pb-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400">
            Service Topology
          </h1>
          <p className="text-text-muted mt-2">Real-time interactive map of all monitored services and active dependencies.</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <span className="w-3 h-3 rounded-full bg-status-healthy mr-2 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
            <span className="text-sm text-text-muted">Healthy</span>
          </div>
          <div className="flex items-center">
            <span className="w-3 h-3 rounded-full bg-status-critical mr-2 shadow-[0_0_8px_rgba(239,68,68,0.5)]"></span>
            <span className="text-sm text-text-muted">Degraded</span>
          </div>
        </div>
      </div>
      
      <div className="flex-1 bg-surface border border-border rounded-xl overflow-hidden relative shadow-lg group">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-indigo-500 opacity-50"></div>
        <ReactFlow 
          nodes={nodes} 
          edges={edges}
          fitView
          attributionPosition="bottom-right"
        >
          <Background color="#E2E8F0" gap={16} />
          <Controls className="bg-surface border-border !fill-text-primary" />
        </ReactFlow>
      </div>
    </div>
  )
}
