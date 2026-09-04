import { useState } from 'react'
import { Map, Loader2, Play } from 'lucide-react'

export function ChangeDetection() {
  const [pairId, setPairId] = useState('')
  const [isDetecting, setIsDetecting] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  const handleRunDetection = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!pairId) return

    setIsDetecting(true)
    setError('')
    try {
      const res = await fetch('http://localhost:8000/change-detection/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pair_id: parseInt(pairId) })
      })
      if (!res.ok) throw new Error('Change detection failed')
      const data = await res.json()
      
      // Immediately fetch the results
      const res2 = await fetch(`http://localhost:8000/change-detection/detections/${data.pair_id}`)
      if (!res2.ok) throw new Error('Failed to fetch detection results')
      const data2 = await res2.json()
      
      setResult({
        ...data,
        features: data2.results
      })
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsDetecting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl glass">
        <h2 className="text-xl font-bold mb-2">Change Detection Pipeline</h2>
        <p className="text-muted-foreground mb-6">
          Run the baseline differencing algorithm on a paired scene to generate vector polygons of detected changes.
        </p>

        <form onSubmit={handleRunDetection} className="flex gap-4">
          <input 
            type="number" 
            value={pairId}
            onChange={(e) => setPairId(e.target.value)}
            placeholder="Enter Pair ID (e.g. 1)"
            className="w-full max-w-xs px-4 py-2 bg-background border border-border/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            min="1"
            required
          />
          <button 
            type="submit" 
            disabled={isDetecting || !pairId}
            className="flex items-center gap-2 px-6 py-2 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {isDetecting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5 fill-current" />}
            <span>Run Detection</span>
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 text-red-500 border border-red-500/20 rounded-lg">
          {error}
        </div>
      )}

      {result && (
        <div className="p-6 rounded-2xl glass space-y-6">
          <div className="flex items-center gap-3 text-emerald-500">
            <Map className="w-6 h-6" />
            <h3 className="text-lg font-bold">Detection Results (Pair {result.pair_id})</h3>
          </div>
          
          <div className="flex gap-8">
            <div><span className="text-muted-foreground">Status:</span> <span className="font-medium capitalize">{result.status}</span></div>
            <div><span className="text-muted-foreground">Polygons Generated:</span> <span className="font-medium">{result.detections_made}</span></div>
          </div>

          {result.features && result.features.length > 0 && (
            <div className="border border-border/50 rounded-lg overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead className="bg-black/5 dark:bg-white/5 text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-medium">ID</th>
                    <th className="px-4 py-3 font-medium">Confidence</th>
                    <th className="px-4 py-3 font-medium">Class</th>
                    <th className="px-4 py-3 font-medium">Geometry (WKT)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {result.features.map((feat: any) => (
                    <tr key={feat.id} className="hover:bg-black/5 dark:hover:bg-white/5">
                      <td className="px-4 py-3 font-medium">{feat.id}</td>
                      <td className="px-4 py-3 text-emerald-500">{(feat.confidence * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 capitalize">{feat.classification}</td>
                      <td className="px-4 py-3 font-mono text-xs truncate max-w-xs">{feat.geom}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
