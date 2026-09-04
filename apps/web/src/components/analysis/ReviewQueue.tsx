import { useState, useEffect } from 'react'
import { CheckSquare, Check, X, AlertTriangle, Loader2 } from 'lucide-react'

export function ReviewQueue() {
  const [queue, setQueue] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchQueue = async () => {
    setIsLoading(true)
    try {
      const res = await fetch('http://localhost:8000/change-detection/queue')
      if (!res.ok) throw new Error('Failed to fetch review queue')
      const data = await res.json()
      setQueue(data.results || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchQueue()
  }, [])

  const handleReview = async (id: number, action: string) => {
    try {
      const res = await fetch(`http://localhost:8000/change-detection/detections/${id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, notes: `Reviewed via web UI` })
      })
      if (!res.ok) throw new Error('Review failed')
      
      // Remove from queue locally
      setQueue(q => q.filter(item => item.id !== id))
    } catch (err: any) {
      alert(err.message)
    }
  }

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl glass flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold mb-2">Analyst Review Queue</h2>
          <p className="text-muted-foreground">
            Audit pending change detections. Confirm true positives or reject false alarms to improve the system.
          </p>
        </div>
        <button
          onClick={fetchQueue}
          disabled={isLoading}
          className="px-4 py-2 bg-secondary text-secondary-foreground font-medium rounded-lg hover:bg-secondary/80 transition-colors disabled:opacity-50"
        >
          {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Refresh Queue'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 text-red-500 border border-red-500/20 rounded-lg">
          {error}
        </div>
      )}

      {queue.length === 0 && !isLoading && !error && (
        <div className="p-12 rounded-2xl glass flex flex-col items-center justify-center min-h-[300px]">
          <CheckSquare className="w-12 h-12 text-emerald-500 mb-4" />
          <h3 className="text-xl font-bold text-foreground">Inbox Zero!</h3>
          <p className="text-muted-foreground">There are no pending detections to review.</p>
        </div>
      )}

      {queue.length > 0 && (
        <div className="grid gap-4">
          {queue.map(item => (
            <div key={item.id} className="p-6 rounded-2xl glass flex flex-col md:flex-row justify-between items-center gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-lg font-bold">Detection #{item.id}</span>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    item.classification === 'high_risk_false_alarm' ? 'bg-amber-500/10 text-amber-500' : 'bg-primary/10 text-primary'
                  }`}>
                    {item.classification.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Temporal Pair: {item.pair_id}</p>
                  <p>Confidence: {(item.confidence * 100).toFixed(1)}%</p>
                  <p className="font-mono text-xs truncate max-w-md" title={item.geom}>{item.geom}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => handleReview(item.id, 'CONFIRM')}
                  className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 rounded-lg transition-colors font-medium"
                >
                  <Check className="w-4 h-4" /> Confirm
                </button>
                <button 
                  onClick={() => handleReview(item.id, 'REJECT')}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition-colors font-medium"
                >
                  <X className="w-4 h-4" /> Reject
                </button>
                <button 
                  onClick={() => handleReview(item.id, 'ESCALATE')}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-500/10 text-purple-500 hover:bg-purple-500/20 rounded-lg transition-colors font-medium"
                >
                  <AlertTriangle className="w-4 h-4" /> Escalate
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
