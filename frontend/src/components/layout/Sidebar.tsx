import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Network, TestTube2, Settings, ShieldAlert } from 'lucide-react'

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Services', path: '/services', icon: Network },
  { name: 'Evaluation', path: '/evaluation', icon: TestTube2 },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="w-64 h-full bg-surface border-r border-border flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-border">
        <ShieldAlert className="text-status-healthy w-6 h-6 mr-3" />
        <span className="text-lg font-bold tracking-wide">Sentinel</span>
      </div>
      
      <div className="flex-1 py-6 px-4 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname.startsWith(item.path)
          const Icon = item.icon
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-4 py-2.5 rounded-md transition-colors text-sm font-medium ${
                isActive 
                  ? 'bg-status-low/10 text-status-low' 
                  : 'text-text-secondary hover:text-text-primary hover:bg-surfaceHover'
              }`}
            >
              <Icon className="w-4 h-4 mr-3" />
              {item.name}
            </Link>
          )
        })}
      </div>
      
      <div className="p-4 border-t border-border">
        <button className="flex items-center w-full px-4 py-2.5 text-text-secondary hover:text-text-primary hover:bg-surfaceHover rounded-md transition-colors text-sm font-medium">
          <Settings className="w-4 h-4 mr-3" />
          Settings
        </button>
      </div>
    </div>
  )
}
