import { 
  LayoutDashboard, 
  Search, 
  Map, 
  Clock, 
  CheckSquare, 
  FileText,
  Download,
  Settings,
  HelpCircle
} from 'lucide-react'

export const navigation = [
  { name: 'Dashboard', id: 'dashboard', icon: LayoutDashboard },
  { name: 'Semantic Search', id: 'search', icon: Search },
  { name: 'Temporal Analysis', id: 'temporal', icon: Clock },
  { name: 'Change Detection', id: 'detection', icon: Map },
  { name: 'Review Queue', id: 'review', icon: CheckSquare },
  { name: 'Exports', id: 'exports', icon: Download },
  { name: 'Reports', id: 'reports', icon: FileText },
]

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  return (
    <div className="flex flex-col w-64 glass border-r border-border/10 h-full relative z-20">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-br from-primary to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-primary/30">
          <Map className="text-white w-5 h-5" />
        </div>
        <span className="text-xl font-bold tracking-tight text-gradient">GeoScope AI</span>
      </div>
      
      <div className="flex-1 overflow-y-auto py-4 px-3">
        <nav className="space-y-1">
          {navigation.map((item) => {
            const isCurrent = item.id === activeTab;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-300 group ${
                  isCurrent 
                    ? 'bg-primary/15 text-primary font-medium shadow-[0_0_15px_rgba(var(--primary),0.1)] border border-primary/20' 
                    : 'text-muted-foreground hover:bg-black/5 dark:hover:bg-white/5 hover:text-foreground hover:translate-x-1'
                }`}
              >
                <item.icon className={`w-5 h-5 transition-transform duration-300 ${isCurrent ? 'text-primary' : 'text-muted-foreground group-hover:scale-110 group-hover:text-primary'}`} />
                {item.name}
              </button>
            )
          })}
        </nav>
      </div>
      
      <div className="p-4 border-t border-border/10 space-y-1">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-black/5 dark:hover:bg-white/5 hover:text-foreground transition-all duration-300 hover:translate-x-1 group">
          <Settings className="w-5 h-5 transition-transform duration-300 group-hover:rotate-90 group-hover:text-primary" />
          Settings
        </button>
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-black/5 dark:hover:bg-white/5 hover:text-foreground transition-all duration-300 hover:translate-x-1 group">
          <HelpCircle className="w-5 h-5 transition-transform duration-300 group-hover:scale-110 group-hover:text-primary" />
          Help & Docs
        </button>
      </div>
    </div>
  )
}
