import { useState } from 'react'
import { Search as SearchIcon, Image as ImageIcon, Loader2 } from 'lucide-react'

export function TileImage({ url, alt }: { url: string, alt: string }) {
  const [status, setStatus] = useState<'loading' | 'loaded' | 'error'>('loading')
  return (
    <div className="relative w-full h-full bg-black/5 dark:bg-white/5 flex items-center justify-center overflow-hidden rounded">
      {status === 'loading' && <Loader2 className="w-6 h-6 animate-spin text-muted-foreground/50 absolute" />}
      {status === 'error' && <div className="text-xs text-muted-foreground">Failed to load image</div>}
      <img
        src={url}
        alt={alt}
        onLoad={() => setStatus('loaded')}
        onError={() => setStatus('error')}
        className={`w-full h-full object-cover transition-opacity duration-300 ${status === 'loaded' ? 'opacity-100' : 'opacity-0'}`}
      />
    </div>
  )
}

export function SemanticSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [hasSearched, setHasSearched] = useState(false)

  const handleTextSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query) return

    setIsLoading(true)
    setError('')
    setHasSearched(false)
    try {
      const res = await fetch('http://localhost:8000/search/semantic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 10 })
      })
      if (!res.ok) throw new Error('Search failed')
      const data = await res.json()
      setResults(data.results || [])
      setHasSearched(true)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleImageSearch = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsLoading(true)
    setError('')
    setHasSearched(false)
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      // Assuming image search takes a limit via query param
      const res = await fetch('http://localhost:8000/search/image?limit=10', {
        method: 'POST',
        body: formData
      })
      if (!res.ok) throw new Error('Image search failed')
      const data = await res.json()
      setResults(data.results || [])
      setHasSearched(true)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl glass">
        <h2 className="text-xl font-bold mb-4">Semantic & Image Search</h2>
        
        <form onSubmit={handleTextSearch} className="flex gap-4 mb-4">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-5 h-5" />
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search satellite imagery (e.g., 'dense forest', 'urban area')..."
              className="w-full pl-10 pr-4 py-2 bg-background border border-border/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <button 
            type="submit" 
            disabled={isLoading}
            className="px-6 py-2 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Search'}
          </button>
        </form>

        <div className="flex items-center gap-4">
          <div className="text-sm text-muted-foreground">Or search by image:</div>
          <label className="cursor-pointer flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors">
            <ImageIcon className="w-4 h-4" />
            <span>Upload Image</span>
            <input type="file" className="hidden" accept="image/*" onChange={handleImageSearch} />
          </label>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 text-red-500 border border-red-500/20 rounded-lg">
          {error}
        </div>
      )}

      {hasSearched && !isLoading && results.length === 0 && !error && (
        <div className="p-6 rounded-2xl glass flex flex-col items-center justify-center min-h-[200px]">
          <SearchIcon className="w-12 h-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium text-foreground">No results found</h3>
          <p className="text-muted-foreground text-center max-w-sm mt-2">
            We couldn't find any satellite imagery matching your search. Try using different keywords or a broader search term.
          </p>
        </div>
      )}

      {results.length > 0 && (
        <div className="p-6 rounded-2xl glass">
          <h3 className="text-lg font-bold mb-4">Results ({results.length})</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((result, i) => (
              <div key={i} className="bg-background border border-border/50 rounded-lg p-4 overflow-hidden">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-mono text-xs text-muted-foreground truncate" title={result.id}>
                    {result.id}
                  </span>
                  <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
                    {(result.similarity_score * 100).toFixed(1)}% match
                  </span>
                </div>
                <div className="text-sm font-medium mb-1">Scene: <span className="font-normal">{result.scene_id}</span></div>
                <div className="text-sm font-medium mb-1 truncate">MinIO: <span className="font-normal">{result.minio_path}</span></div>
                <div className="text-sm font-medium mb-1">Type: <span className="font-normal text-muted-foreground">Satellite Tile</span></div>
                <div className="mt-4 aspect-video rounded flex items-center justify-center">
                  <TileImage url={result.image_url} alt={`Satellite tile ${result.id}`} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
