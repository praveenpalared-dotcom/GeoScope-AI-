import { useState, useEffect } from 'react'
import { Sidebar, navigation } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { SemanticSearch } from './components/search/SemanticSearch'
import { TemporalAnalysis } from './components/analysis/TemporalAnalysis'
import { ChangeDetection } from './components/analysis/ChangeDetection'
import { ReviewQueue } from './components/analysis/ReviewQueue'
import { ExportManager } from './components/exports/ExportManager'
import { ReportsDashboard } from './components/reports/ReportsDashboard'
import { MapViewer } from './components/map/MapViewer'
import { Activity, Layers, Server, ShieldAlert } from 'lucide-react'

interface DashboardMetrics {
  active_scenes: number;
  active_scenes_trend: string;
  change_detections: number;
  awaiting_review: number;
  infrastructure_status: string;
  infrastructure_detail: string;
}

function App() {
  const [status, setStatus] = useState<string>("loading...")
  const [activeTab, setActiveTab] = useState<string>('dashboard')
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)

  useEffect(() => {
    const checkStatus = () => {
      fetch('http://localhost:8000/system/status')
        .then(res => res.json())
        .then(data => setStatus(data.status))
        .catch(() => setStatus("offline"))
        
      fetch('http://localhost:8000/dashboard/metrics')
        .then(res => res.json())
        .then(data => setMetrics(data))
        .catch(console.error)
    }

    checkStatus() // initial check
    const interval = setInterval(checkStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const currentTabName = navigation.find(n => n.id === activeTab)?.name || 'Dashboard'

  return (
    <div className="flex h-screen bg-background overflow-hidden selection:bg-primary/30">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <div className="flex-1 flex flex-col h-full overflow-hidden relative z-10">
        <Header />
        
        <main className="flex-1 overflow-y-auto p-8 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] bg-fixed">
          <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            
            <div className="flex flex-col gap-2">
              <h1 className="text-4xl font-extrabold tracking-tight text-gradient">{currentTabName}</h1>
              <p className="text-muted-foreground text-lg">
                {activeTab === 'dashboard' 
                  ? 'Overview of geospatial intelligence platform metrics.' 
                  : `Currently viewing the ${currentTabName} interface.`}
              </p>
            </div>

            {activeTab === 'dashboard' && (
              <div className="space-y-6">
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                  <div className="p-6 rounded-2xl glass card-hover group cursor-default">
                    <div className="flex flex-row items-center justify-between pb-2">
                      <h3 className="tracking-tight text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">Active Scenes</h3>
                      <div className="p-2 bg-blue-500/10 rounded-lg group-hover:bg-blue-500/20 transition-colors">
                        <Layers className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-foreground mt-2">{metrics?.active_scenes || '0'}</div>
                    <p className="text-xs text-blue-600/80 dark:text-blue-400/80 mt-2 font-medium">{metrics?.active_scenes_trend || 'Live updating'}</p>
                  </div>
                  
                  <div className="p-6 rounded-2xl glass card-hover group cursor-default">
                    <div className="flex flex-row items-center justify-between pb-2">
                      <h3 className="tracking-tight text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">Pending Detections</h3>
                      <div className="p-2 bg-amber-500/10 rounded-lg group-hover:bg-amber-500/20 transition-colors">
                        <ShieldAlert className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-foreground mt-2">{metrics?.awaiting_review || '0'}</div>
                    <p className="text-xs text-amber-600/80 dark:text-amber-400/80 mt-2 font-medium">Awaiting analyst action</p>
                  </div>
                  
                  <div className="p-6 rounded-2xl glass card-hover group cursor-default">
                    <div className="flex flex-row items-center justify-between pb-2">
                      <h3 className="tracking-tight text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">API Status</h3>
                      <div className="p-2 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                        <Activity className="h-5 w-5 text-primary" />
                      </div>
                    </div>
                    <div className="flex items-center gap-3 mt-3">
                      <div className="relative flex h-3 w-3">
                        {status === 'online' ? (
                          <>
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                          </>
                        ) : (
                          <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                        )}
                      </div>
                      <div className="text-2xl font-bold text-foreground capitalize">{status}</div>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl glass card-hover group cursor-default">
                    <div className="flex flex-row items-center justify-between pb-2">
                      <h3 className="tracking-tight text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">Infrastructure</h3>
                      <div className="p-2 bg-purple-500/10 rounded-lg group-hover:bg-purple-500/20 transition-colors">
                        <Server className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-foreground mt-3">{metrics?.infrastructure_status || 'Online'}</div>
                    <p className="text-xs text-muted-foreground mt-2 font-medium">{metrics?.infrastructure_detail || 'All systems nominal'}</p>
                  </div>
                </div>

                <div className="p-6 rounded-2xl glass">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h2 className="text-xl font-bold text-foreground">Global Operating Picture</h2>
                      <p className="text-sm text-muted-foreground">Interactive map of all spatial detection hotspots across regions</p>
                    </div>
                  </div>
                  <MapViewer geoJsonUrl="http://localhost:8000/exports/clusters" className="w-full h-[500px] rounded-xl overflow-hidden shadow-lg border border-border/50" />
                </div>
              </div>
            )}

            {activeTab === 'search' && <SemanticSearch />}
            {activeTab === 'temporal' && <TemporalAnalysis />}
            {activeTab === 'detection' && <ChangeDetection />}
            {activeTab === 'review' && <ReviewQueue />}
            {activeTab === 'exports' && <ExportManager />}

            {activeTab === 'reports' && <ReportsDashboard />}
            
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
