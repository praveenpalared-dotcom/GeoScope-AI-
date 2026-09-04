import { useState } from 'react'
import { Clock, Loader2, Server } from 'lucide-react'

export function TemporalAnalysis() {
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  const handlePairScenes = async () => {
    setIsLoading(true)
    setError('')
    try {
      const res = await fetch('http://localhost:8000/temporal/pair', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}) // AOI can be added later
      })
      if (!res.ok) throw new Error('Failed to generate temporal pairs')
      const data = await res.json()
      setResult(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl glass flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold mb-2">Temporal Engine</h2>
          <p className="text-muted-foreground">
            Automatically pair intersecting satellite scenes across different times to prepare for change detection.
          </p>
        </div>
        <button
          onClick={handlePairScenes}
          disabled={isLoading}
          className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Clock className="w-5 h-5" />}
          <span>Generate Pairs</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 text-red-500 border border-red-500/20 rounded-lg">
          {error}
        </div>
      )}

      {result && (
        <div className="p-6 rounded-2xl glass">
          <div className="flex items-center gap-3 mb-4 text-emerald-500">
            <Server className="w-6 h-6" />
            <h3 className="text-lg font-bold">Pairing Complete</h3>
          </div>
          <div className="space-y-2">
            <p><span className="font-medium text-foreground">Status:</span> {result.status}</p>
            <p><span className="font-medium text-foreground">Pairs Created:</span> {result.pairs_created}</p>
          </div>
        </div>
      )}
    </div>
  )
}
