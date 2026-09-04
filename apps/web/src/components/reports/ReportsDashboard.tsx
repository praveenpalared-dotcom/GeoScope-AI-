import { useState, useEffect } from 'react'
import { Activity, BarChart2, PieChart as PieChartIcon } from 'lucide-react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'

export function ReportsDashboard() {
  const [classificationData, setClassificationData] = useState([])
  const [statusData, setStatusData] = useState([])
  const [timelineData, setTimelineData] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#a855f7']

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const [resClass, resStatus, resTimeline] = await Promise.all([
          fetch('http://localhost:8000/reports/detections/classification'),
          fetch('http://localhost:8000/reports/detections/status'),
          fetch('http://localhost:8000/reports/scenes/timeline')
        ])

        if (!resClass.ok || !resStatus.ok || !resTimeline.ok) {
          throw new Error('Failed to fetch report data')
        }

        setClassificationData(await resClass.json())
        setStatusData(await resStatus.json())
        setTimelineData(await resTimeline.json())
      } catch (err: any) {
        setError(err.message)
      } finally {
        setIsLoading(false)
      }
    }

    fetchReports()
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500/10 text-red-500 border border-red-500/20 rounded-lg">
        {error}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Classification & Status Row */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Classification Chart */}
        <div className="p-6 rounded-2xl glass flex flex-col h-[400px]">
          <div className="flex items-center gap-2 mb-6">
            <PieChartIcon className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-bold text-foreground">Detections by Classification</h3>
          </div>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={classificationData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {classificationData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Chart */}
        <div className="p-6 rounded-2xl glass flex flex-col h-[400px]">
          <div className="flex items-center gap-2 mb-6">
            <BarChart2 className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-bold text-foreground">Detections by Status</h3>
          </div>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
                  cursor={{ fill: 'hsl(var(--muted))', opacity: 0.2 }}
                />
                <Bar dataKey="value" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Timeline Row */}
      <div className="p-6 rounded-2xl glass flex flex-col h-[400px]">
        <div className="flex items-center gap-2 mb-6">
          <Activity className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-bold text-foreground">Scenes Ingested (Last 30 Days)</h3>
        </div>
        <div className="flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" />
              <YAxis stroke="hsl(var(--muted-foreground))" />
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
                cursor={{ fill: 'hsl(var(--muted))', opacity: 0.2 }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  )
}
