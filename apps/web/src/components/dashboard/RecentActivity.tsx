import { AlertCircle, MapPin, Search } from 'lucide-react'

const activities = [
  {
    id: 1,
    title: 'High-confidence change detected',
    description: 'New construction footprint identified in Sector 7-G.',
    time: '2 minutes ago',
    icon: AlertCircle,
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10'
  },
  {
    id: 2,
    title: 'Semantic search completed',
    description: 'Query "military aircraft parked on tarmac" yielded 14 results.',
    time: '1 hour ago',
    icon: Search,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10'
  },
  {
    id: 3,
    title: 'New scene ingested',
    description: 'Sentinel-2 L2A tile 43QEG added to standard index.',
    time: '3 hours ago',
    icon: MapPin,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10'
  }
]

export function RecentActivity() {
  return (
    <div className="space-y-6 mt-4">
      {activities.map((activity) => (
        <div key={activity.id} className="flex gap-4">
          <div className={`mt-0.5 w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${activity.bgColor}`}>
            <activity.icon className={`w-4 h-4 ${activity.color}`} />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">{activity.title}</p>
            <p className="text-sm text-muted-foreground mt-0.5">{activity.description}</p>
            <p className="text-xs text-muted-foreground mt-1.5">{activity.time}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
