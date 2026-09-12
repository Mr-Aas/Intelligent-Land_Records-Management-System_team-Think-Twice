import React, { useEffect, useState } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import { Layers, Eye, EyeOff, Info } from 'lucide-react';
import type { GeoJSONFeature, GeoJSONFeatureCollection, StructureProperties } from '../types';

interface GISMapProps {
  cadastralLayer: GeoJSONFeatureCollection | null;
  municipalLayer: GeoJSONFeatureCollection | null;
  reviewStructuresLayer: GeoJSONFeatureCollection<StructureProperties> | null;
  selectedFeature: GeoJSONFeature | null;
  onSelectFeature: (feature: GeoJSONFeature) => void;
}

// Map center adjuster on selection
const MapController: React.FC<{
  selectedFeature: GeoJSONFeature | null;
}> = ({ selectedFeature }) => {
  const map = useMap();

  useEffect(() => {
    if (selectedFeature && selectedFeature.geometry) {
      try {
        const layer = L.geoJSON(selectedFeature as any);
        const bounds = layer.getBounds();
        if (bounds.isValid()) {
          map.flyToBounds(bounds, { maxZoom: 18, duration: 1.2, padding: [60, 60] });
        }
      } catch (err) {
        console.error('Error centering map on feature:', err);
      }
    }
  }, [selectedFeature, map]);

  return null;
};

export const GISMap: React.FC<GISMapProps> = ({
  cadastralLayer,
  municipalLayer,
  reviewStructuresLayer,
  selectedFeature,
  onSelectFeature,
}) => {
  // Layer visibility toggles (QGIS layer panel style)
  const [showCadastral, setShowCadastral] = useState(true);
  const [showMunicipal, setShowMunicipal] = useState(true);
  const [showStructures, setShowStructures] = useState(true);
  const [layerPanelOpen, setLayerPanelOpen] = useState(false);

  // Default coordinate center (UTM 44N / Kumaon Haldwani / Synthetic centroid)
  const defaultCenter: [number, number] = [29.2183, 79.513];

  // Cadastral styling
  const cadastralStyle = (feature: any) => {
    const isSelected =
      selectedFeature?.properties?.parcel_id === feature?.properties?.parcel_id;
    return {
      color: isSelected ? '#38bdf8' : '#6366f1',
      weight: isSelected ? 3 : 1.5,
      opacity: 0.9,
      fillColor: isSelected ? '#38bdf8' : '#4f46e5',
      fillOpacity: isSelected ? 0.25 : 0.08,
      dashArray: '3, 3',
    };
  };

  // Municipal building styling
  const municipalStyle = () => ({
    color: '#94a3b8',
    weight: 1,
    opacity: 0.8,
    fillColor: '#cbd5e1',
    fillOpacity: 0.15,
  });

  // Review structure styling
  const structureStyle = (feature: any) => {
    const props: StructureProperties = feature?.properties || {};
    const isSelected =
      selectedFeature?.properties?.structure_id === props.structure_id;

    let color = '#10b981'; // verified green
    let fillColor = '#10b981';

    if (props.status === 'audit_pending') {
      color = '#f59e0b'; // amber
      fillColor = '#f59e0b';
    } else if (props.status === 'disputed') {
      color = '#ef4444'; // red
      fillColor = '#ef4444';
    } else if (props.status === 'locked_disputed') {
      color = '#8b5cf6'; // purple
      fillColor = '#8b5cf6';
    }

    return {
      color: isSelected ? '#ffffff' : color,
      weight: isSelected ? 3.5 : 2,
      opacity: 1.0,
      fillColor,
      fillOpacity: isSelected ? 0.6 : 0.35,
    };
  };

  return (
    <div className="relative flex-1 h-full w-full bg-slate-950 overflow-hidden">
      <MapContainer
        center={defaultCenter}
        zoom={16}
        className="w-full h-full z-10"
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url='https://tile.openstreetmap.org/{z}/{x}/{y}.png'
          maxZoom={20}
        />



        <MapController selectedFeature={selectedFeature} />

        {/* 1. Cadastral Parcels Layer */}
        {showCadastral && cadastralLayer && (
          <GeoJSON
            key={`cadastral-${cadastralLayer.features.length}`}
            data={cadastralLayer as any}
            style={cadastralStyle}
            onEachFeature={(feature, layer) => {
              const p = feature.properties || {};
              layer.bindTooltip(
                `<strong>Parcel:</strong> ${p.parcel_id || 'N/A'}<br/><strong>Khasra:</strong> ${p.khasra_no || 'N/A'}<br/><strong>Tehsil:</strong> ${p.tehsil || 'N/A'}`,
                { className: 'bg-slate-900 text-white text-xs border border-slate-700', sticky: true }
              );
              layer.on('click', () => onSelectFeature(feature as any));
            }}
          />
        )}

        {/* 2. Municipal Buildings Layer */}
        {showMunicipal && municipalLayer && (
          <GeoJSON
            key={`municipal-${municipalLayer.features.length}`}
            data={municipalLayer as any}
            style={municipalStyle}
            onEachFeature={(feature, layer) => {
              const p = feature.properties || {};
              layer.bindTooltip(
                `<strong>Municipal ID:</strong> ${p.municipal_building_id || 'N/A'}<br/><strong>Status:</strong> ${p.building_status || 'registered'}`,
                { className: 'bg-slate-900 text-white text-xs border border-slate-700', sticky: true }
              );
              layer.on('click', () => onSelectFeature(feature as any));
            }}
          />
        )}

        {/* 3. Review Structures Layer */}
        {showStructures && reviewStructuresLayer && (
          <GeoJSON
            key={`structures-${reviewStructuresLayer.features.length}-${selectedFeature?.properties?.structure_id}`}
            data={reviewStructuresLayer as any}
            style={structureStyle}
            onEachFeature={(feature, layer) => {
              const p: StructureProperties = feature.properties || {};
              layer.bindTooltip(
                `<strong>Structure:</strong> ${p.structure_id}<br/><strong>Status:</strong> ${p.status}<br/><strong>Overflow:</strong> ${p.overflow_measure !== undefined ? `${p.overflow_measure}m` : '0m'}`,
                { className: 'bg-slate-900 text-white text-xs border border-slate-700', sticky: true }
              );
              layer.on('click', () => onSelectFeature(feature as any));
            }}
          />
        )}
      </MapContainer>

      {/* Floating QGIS Layer Switcher Panel */}
      <div className="absolute top-4 right-4 z-20 flex flex-col items-end">
        <button
          onClick={() => setLayerPanelOpen(!layerPanelOpen)}
          className="flex items-center gap-2 bg-slate-900/90 hover:bg-slate-800 text-white px-3 py-2 rounded-lg border border-slate-700/80 shadow-lg text-xs font-semibold backdrop-blur transition"
        >
          <Layers className="w-4 h-4 text-indigo-400" />
          <span>GIS Layers</span>
        </button>

        {layerPanelOpen && (
          <div className="mt-2 w-64 bg-slate-900/95 border border-slate-700/80 rounded-lg p-3 shadow-2xl backdrop-blur text-xs space-y-2.5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 font-bold text-slate-200">
              <span>Layer Visibility</span>
              <span className="text-[10px] text-slate-400">Toggle ON/OFF</span>
            </div>

            {/* Cadastral Layer Toggle */}
            <label className="flex items-center justify-between cursor-pointer group">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-sm border border-indigo-400 bg-indigo-500/20"></span>
                <span className="text-slate-300 group-hover:text-white">Cadastral Parcels</span>
              </div>
              <button
                onClick={() => setShowCadastral(!showCadastral)}
                className="text-slate-400 hover:text-white"
              >
                {showCadastral ? <Eye className="w-4 h-4 text-indigo-400" /> : <EyeOff className="w-4 h-4 text-slate-600" />}
              </button>
            </label>

            {/* Municipal Layer Toggle */}
            <label className="flex items-center justify-between cursor-pointer group">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-sm border border-slate-400 bg-slate-400/20"></span>
                <span className="text-slate-300 group-hover:text-white">Municipal Records</span>
              </div>
              <button
                onClick={() => setShowMunicipal(!showMunicipal)}
                className="text-slate-400 hover:text-white"
              >
                {showMunicipal ? <Eye className="w-4 h-4 text-slate-300" /> : <EyeOff className="w-4 h-4 text-slate-600" />}
              </button>
            </label>

            {/* Review Structures Layer Toggle */}
            <label className="flex items-center justify-between cursor-pointer group">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-sm border border-amber-400 bg-amber-400/30"></span>
                <span className="text-slate-300 group-hover:text-white">Physical Structures</span>
              </div>
              <button
                onClick={() => setShowStructures(!showStructures)}
                className="text-slate-400 hover:text-white"
              >
                {showStructures ? <Eye className="w-4 h-4 text-amber-400" /> : <EyeOff className="w-4 h-4 text-slate-600" />}
              </button>
            </label>

            {/* Map Legend */}
            <div className="border-t border-slate-800 pt-2 space-y-1 text-[11px] text-slate-400">
              <div className="font-semibold text-slate-300 mb-1">Status Legend</div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <span>Verified (GeoAI / Lekhpal)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                <span>Audit Pending (10m–20m)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
                <span>Disputed (&gt;20m / Multi-parcel)</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Floating Feature Inspector Drawer if a feature is selected */}
      {selectedFeature && (
        <div className="absolute bottom-4 left-4 right-4 max-w-xl mx-auto z-20 bg-slate-900/95 border border-indigo-500/50 rounded-xl p-3.5 shadow-2xl backdrop-blur text-xs">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-indigo-400" />
              <span className="font-bold text-slate-100">
                {selectedFeature.properties?.structure_id
                  ? `Structure Inspector: ${selectedFeature.properties.structure_id}`
                  : `Cadastral Parcel: ${selectedFeature.properties.parcel_id}`}
              </span>
            </div>
            <span className="text-[10px] bg-slate-800 border border-slate-700 text-indigo-300 font-semibold px-2 py-0.5 rounded uppercase">
              {selectedFeature.properties?.status || 'Cadastral Parcel'}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 bg-slate-950/80 p-2 rounded-lg border border-slate-800/80 text-[11px]">
            <div>
              <span className="text-slate-500 block">Assigned Tehsil:</span>
              <span className="text-slate-200 font-medium">
                {selectedFeature.properties?.cadastral_record?.tehsil ||
                  selectedFeature.properties?.tehsil ||
                  'N/A'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Khasra / Khata:</span>
              <span className="text-slate-200 font-medium">
                {selectedFeature.properties?.cadastral_record?.khasra_no ||
                  selectedFeature.properties?.khasra_no ||
                  'N/A'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Overflow / Area:</span>
              <span className="text-amber-400 font-bold">
                {selectedFeature.properties?.overflow_measure !== undefined
                  ? `${selectedFeature.properties.overflow_measure} m overflow`
                  : `${selectedFeature.properties?.record_area_sqm || 'N/A'} sqm`}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
