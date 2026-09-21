import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function MainLayout() {
  return (
    <div className="flex h-screen w-screen bg-background overflow-hidden">
      <Sidebar />
      
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar />
        
        <main className="flex-1 overflow-y-auto p-6 relative">
          {/* Main content injected here via React Router */}
          <Outlet />
        </main>
      </div>
    </div>
  )
}
