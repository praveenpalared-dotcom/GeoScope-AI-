import { Download, FileJson } from 'lucide-react'

export function ExportManager() {
  const downloadGeoJSON = async (type: 'detections' | 'clusters') => {
    try {
      const res = await fetch(`http://localhost:8000/exports/${type}`)
      if (!res.ok) throw new Error(`Failed to export ${type}`)
      const data = await res.json()
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/geo+json' })
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = `${type}_export_${new Date().toISOString().split('T')[0]}.geojson`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err: any) {
      alert(err.message)
    }
  }

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl glass">
        <h2 className="text-xl font-bold mb-2">Data Exports</h2>
        <p className="text-muted-foreground mb-6">
          Download your geospatial intelligence data in standard formats for use in QGIS, ArcGIS, or other external tools.
        </p>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="p-6 border border-border/50 rounded-xl bg-background/50 flex flex-col items-start gap-4">
            <div className="p-3 bg-blue-500/10 text-blue-500 rounded-lg">
              <FileJson className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Change Detections</h3>
              <p className="text-sm text-muted-foreground">Export all confirmed and pending change detection polygons as GeoJSON.</p>
            </div>
            <button 
              onClick={() => downloadGeoJSON('detections')}
              className="mt-2 flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground font-medium rounded-lg hover:bg-secondary/80 transition-colors"
            >
              <Download className="w-4 h-4" /> Download GeoJSON
            </button>
          </div>

          <div className="p-6 border border-border/50 rounded-xl bg-background/50 flex flex-col items-start gap-4">
            <div className="p-3 bg-purple-500/10 text-purple-500 rounded-lg">
              <FileJson className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Detection Clusters</h3>
              <p className="text-sm text-muted-foreground">Export the regional hotspots and spatial clusters as GeoJSON polygons.</p>
            </div>
            <button 
              onClick={() => downloadGeoJSON('clusters')}
              className="mt-2 flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground font-medium rounded-lg hover:bg-secondary/80 transition-colors"
            >
              <Download className="w-4 h-4" /> Download GeoJSON
            </button>
          </div>
        </div>
      </div>
      
      <div className="p-6 rounded-2xl glass">
         <h2 className="text-xl font-bold mb-2">Tile Serving</h2>
         <p className="text-muted-foreground mb-4">
           The platform now supports on-the-fly XYZ-style raster serving for all ingested tiles.
         </p>
         <code className="block p-4 bg-black/10 dark:bg-white/5 rounded-lg text-sm text-primary font-mono overflow-x-auto">
            GET http://localhost:8000/tiles/&#123;scene_id&#125;/&#123;tile_id&#125;.png
         </code>
      </div>
    </div>
  )
}
