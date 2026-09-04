import { Bell, Search, User, Moon, Sun } from 'lucide-react'
import { useState, useEffect } from 'react'

export function Header() {
  const [isDark, setIsDark] = useState(true)

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  return (
    <header className="h-16 border-b border-border/10 glass flex items-center justify-between px-6 z-10 relative">
      <div className="flex items-center flex-1">
        <div className="relative w-96 group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground transition-colors group-focus-within:text-primary" />
          <input
            type="text"
            placeholder="Search scenes, locations, or coordinates..."
            className="w-full bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 rounded-full pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:bg-black/10 dark:focus:bg-white/10 text-foreground transition-all duration-300"
          />
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <button 
          onClick={() => setIsDark(!isDark)}
          className="relative p-2.5 text-muted-foreground hover:bg-black/10 dark:hover:bg-white/10 hover:text-foreground rounded-full transition-all duration-300 hover:scale-110"
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        <button className="relative p-2.5 text-muted-foreground hover:bg-black/10 dark:hover:bg-white/10 hover:text-foreground rounded-full transition-all duration-300 hover:scale-110">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-destructive rounded-full ring-2 ring-card animate-pulse"></span>
        </button>

        <div className="h-9 w-9 bg-gradient-to-br from-primary/20 to-primary/40 border border-primary/30 rounded-full flex items-center justify-center text-primary font-medium cursor-pointer transition-all duration-300 hover:scale-110 hover:shadow-[0_0_15px_rgba(var(--primary),0.3)]">
          <User className="w-4 h-4" />
        </div>
      </div>
    </header>
  )
}
