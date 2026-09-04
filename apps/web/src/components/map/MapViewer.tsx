import { useEffect, useRef, useState, useCallback } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

interface MapViewerProps {
  geoJsonUrl?: string; // e.g., 'http://localhost:8000/exports/clusters'
  geoJsonData?: any;   // direct GeoJSON object
  className?: string;
}

export interface SatelliteBounds {
  west: number;
  south: number;
  east: number;
  north: number;
}

export interface SatelliteTile {
  id: string;
  scene_id: string;
  image_url: string;
  bounds: SatelliteBounds;
}

export interface SatelliteTilesResponse {
  status: string;
  scene_id: string;
  tiles: SatelliteTile[];
}

export function MapViewer({ geoJsonUrl, geoJsonData, className = "w-full h-[600px] rounded-xl overflow-hidden relative" }: MapViewerProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  
  const [showSatellite, setShowSatellite] = useState(true)
  const [tiles, setTiles] = useState<SatelliteTile[]>([])
  const [status, setStatus] = useState<'idle' | 'loading' | 'error' | 'success'>('idle')
  const didFitBounds = useRef(false)
  const currentSceneId = useRef<string | null>(null)

  useEffect(() => {
    if (map.current || !mapContainer.current) return

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'osm': {
            type: 'raster',
            tiles: [
              'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap Contributors'
          }
        },
        layers: [
          {
            id: 'osm',
            type: 'raster',
            source: 'osm',
            minzoom: 0,
            maxzoom: 22
          }
        ]
      },
      center: [0, 0], // Default center
      zoom: 2
    })

    map.current.on('load', () => {
      setMapLoaded(true)
    })

    map.current.on('error', (e) => {
      if (e.sourceId && e.sourceId.startsWith('satellite-')) {
        console.error("Satellite tile failed:", e.sourceId, e)
      }
    })

    return () => {
      map.current?.remove()
      map.current = null
    }
  }, [])

  // Load geojson data
  useEffect(() => {
    if (!mapLoaded || !map.current) return

    const sourceId = 'geoscope-data'
    
    // Determine the data to use
    let dataToLoad: any = null
    if (geoJsonUrl) {
      dataToLoad = geoJsonUrl
    } else if (geoJsonData) {
      dataToLoad = geoJsonData
    } else {
      return
    }

    // Add or update source
    if (map.current.getSource(sourceId)) {
      (map.current.getSource(sourceId) as maplibregl.GeoJSONSource).setData(dataToLoad)
    } else {
      map.current.addSource(sourceId, {
        type: 'geojson',
        data: dataToLoad
      })

      // Add polygon fill layer
      map.current.addLayer({
        id: 'geoscope-fill',
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': '#3b82f6', // blue-500
          'fill-opacity': 0.4
        }
      })

      // Add polygon outline layer
      map.current.addLayer({
        id: 'geoscope-line',
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#2563eb', // blue-600
          'line-width': 2
        }
      })

      // Add popup on click
      map.current.on('click', 'geoscope-fill', (e) => {
        if (!e.features || e.features.length === 0) return
        const properties = e.features[0].properties
        
        let html = '<div class="p-2 text-black">'
        html += `<h3 class="font-bold mb-1">Feature Details</h3>`
        for (const [key, value] of Object.entries(properties)) {
          html += `<p class="text-sm"><strong>${key}:</strong> ${value}</p>`
        }
        html += '</div>'

        new maplibregl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(html)
          .addTo(map.current!)
      })

      // Change cursor on hover
      map.current.on('mouseenter', 'geoscope-fill', () => {
        map.current!.getCanvas().style.cursor = 'pointer'
      })
      map.current.on('mouseleave', 'geoscope-fill', () => {
        map.current!.getCanvas().style.cursor = ''
      })
    }
  }, [mapLoaded, geoJsonUrl, geoJsonData])

  // Fetch satellite data
  useEffect(() => {
    setStatus('loading')
    fetch('http://localhost:8000/satellite/scenes/SCENE_9e8c86c9/tiles')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch')
        return res.json()
      })
      .then((data: SatelliteTilesResponse) => {
        if (data.status === 'success' && data.tiles) {
          // TASK 1: Log every tile
          console.table(
            data.tiles.map(tile => ({
              id: tile.id,
              west: tile.bounds.west,
              south: tile.bounds.south,
              east: tile.bounds.east,
              north: tile.bounds.north,
              image_url: tile.image_url
            }))
          )

          // TASK 2 & 5: Verify tile geometry & image loading
          data.tiles.forEach(tile => {
            const width = tile.bounds.east - tile.bounds.west;
            const height = tile.bounds.north - tile.bounds.south;
            console.log("Tile geometry", tile.id, { width, height });

            const image = new Image();
            image.onload = () => {
              console.log("Satellite image loaded", {
                tile: tile.id,
                width: image.naturalWidth,
                height: image.naturalHeight
              });
            };
            image.onerror = () => {
              console.error("Satellite image FAILED", {
                tile: tile.id,
                url: tile.image_url
              });
            };
            // trigger load
            image.src = tile.image_url;
          });

          if (currentSceneId.current !== data.scene_id) {
             didFitBounds.current = false;
             currentSceneId.current = data.scene_id;
          }
          setTiles(data.tiles)
          setStatus('success')
        } else {
          setStatus('error')
        }
      })
      .catch(err => {
        console.error("Failed to load satellite scene:", err)
        setStatus('error')
      })
  }, [])

  const focusSatellite = useCallback(() => {
    if (!map.current || tiles.length === 0) return;
    
    const bounds = new maplibregl.LngLatBounds();
    tiles.forEach(tile => {
      bounds.extend([
        [tile.bounds.west, tile.bounds.south],
        [tile.bounds.east, tile.bounds.north]
      ]);
    });

    map.current.fitBounds(bounds, {
      padding: 40,
      maxZoom: 13,
      duration: 800
    })
  }, [tiles])

  // Manage satellite layers
  useEffect(() => {
    if (!mapLoaded || !map.current || tiles.length === 0) return
    const currentMap = map.current

    let minWest = 180, minSouth = 90, maxEast = -180, maxNorth = -90;
    let hasBounds = false;
    let sourcesCount = 0;
    let layersCount = 0;

    const bounds = new maplibregl.LngLatBounds();

    tiles.forEach(tile => {
      const sourceId = `satellite-${tile.id}`
      const layerId = `satellite-layer-${tile.id}`
      const { west, south, east, north } = tile.bounds

      if (west < minWest) minWest = west;
      if (south < minSouth) minSouth = south;
      if (east > maxEast) maxEast = east;
      if (north > maxNorth) maxNorth = north;
      hasBounds = true;

      // Extend bounds using MapLibre's LngLatBounds
      bounds.extend([
        [west, south],
        [east, north]
      ]);

      if (currentMap.getSource(sourceId)) {
        console.warn("Source already exists:", sourceId);
      } else {
        currentMap.addSource(sourceId, {
          type: 'image',
          url: tile.image_url,
          coordinates: [
            [west, north], // top-left
            [east, north], // top-right
            [east, south], // bottom-right
            [west, south]  // bottom-left
          ]
        })
        console.log("Added satellite source:", sourceId);
        sourcesCount++;
      }

      if (currentMap.getLayer(layerId)) {
        console.warn("Layer already exists:", layerId);
      } else {
        // Place satellite imagery underneath geoscope-fill if it exists
        const beforeId = currentMap.getLayer('geoscope-fill') ? 'geoscope-fill' : undefined;
        
        currentMap.addLayer({
          id: layerId,
          type: 'raster',
          source: sourceId,
          layout: {
            'visibility': showSatellite ? 'visible' : 'none'
          },
          paint: {
            'raster-opacity': 0.8 // TASK 7: Temporarily 0.8
          }
        }, beforeId)
        console.log("Added satellite layer:", layerId);
        layersCount++;
      }
      
      // TASK 9: Verify visibility
      const visibility = currentMap.getLayoutProperty(layerId, "visibility");
      console.log(`Layer ${layerId} visibility:`, visibility);
    })

    if (hasBounds && !didFitBounds.current) {
      // TASK 3: FULL SATELLITE EXTENT
      console.log("FULL SATELLITE EXTENT", {
        minWest,
        minSouth,
        maxEast,
        maxNorth,
        width: maxEast - minWest,
        height: maxNorth - minSouth
      })
      
      // Print counts
      console.log(`Total sources added this run: ${sourcesCount}`);
      console.log(`Total layers added this run: ${layersCount}`);

      // TASK 8: Fit map using extended bounds
      currentMap.fitBounds(bounds, {
        padding: 50,
        maxZoom: 14,
        duration: 1000
      })
      didFitBounds.current = true;
    }

  }, [mapLoaded, tiles]) // Re-run if tiles load after map
  
  // Clean up satellite layers on unmount
  useEffect(() => {
    return () => {
        if (map.current) {
            tiles.forEach(tile => {
                const sourceId = `satellite-${tile.id}`
                const layerId = `satellite-layer-${tile.id}`
                if (map.current?.getLayer(layerId)) map.current.removeLayer(layerId)
                if (map.current?.getSource(sourceId)) map.current.removeSource(sourceId)
            })
        }
    }
  }, [tiles])

  useEffect(() => {
      // Toggle visibility when state changes
      if (!mapLoaded || !map.current) return;
      tiles.forEach(tile => {
        const layerId = `satellite-layer-${tile.id}`
        if (map.current?.getLayer(layerId)) {
            map.current.setLayoutProperty(layerId, 'visibility', showSatellite ? 'visible' : 'none')
        }
      })
  }, [showSatellite, mapLoaded, tiles])

  return (
    <div className={className}>
      <div ref={mapContainer} className="w-full h-full" />
      
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 pointer-events-none">
        {status === 'loading' && (
          <div className="bg-primary/90 text-primary-foreground px-4 py-2 rounded-full shadow-lg text-sm font-medium animate-pulse">
            Loading satellite imagery...
          </div>
        )}
        {status === 'error' && (
          <div className="bg-destructive/90 text-destructive-foreground px-4 py-2 rounded-full shadow-lg text-sm font-medium">
            Satellite imagery unavailable
          </div>
        )}
      </div>

      {status === 'success' && tiles.length > 0 && (
        <div className="absolute top-4 right-4 bg-background/90 backdrop-blur border border-border rounded-lg p-4 shadow-lg min-w-[250px] z-10 text-sm">
          <div className="flex justify-between items-center mb-3 pb-2 border-b border-border/50">
            <h3 className="font-bold">Satellite Imagery</h3>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                className="sr-only peer" 
                checked={showSatellite}
                onChange={(e) => setShowSatellite(e.target.checked)}
              />
              <div className="w-9 h-5 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
          
          <div className="space-y-2">
            <div className="font-bold text-primary mb-2">REAL SATELLITE IMAGERY</div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Source:</span>
              <span className="font-medium">Sentinel-2</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Scene:</span>
              <span className="font-medium truncate max-w-[120px]" title="SCENE_9e8c86c9">SCENE_9e8c86c9</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Tiles:</span>
              <span className="font-medium">{tiles.length}</span>
            </div>
            <button 
              onClick={focusSatellite}
              className="w-full mt-2 py-1.5 px-3 bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded text-xs font-medium transition-colors cursor-pointer"
            >
              Focus
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
