import React, { useEffect, useState } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import { Layers, Eye, EyeOff, Info, Menu } from 'lucide-react';
import type { GeoJSONFeature, GeoJSONFeatureCollection, StructureProperties } from '../types';

interface GISMapProps {
  cadastralLayer: GeoJSONFeatureCollection | null;
  municipalLayer: GeoJSONFeatureCollection | null;
  reviewStructuresLayer: GeoJSONFeatureCollection<StructureProperties> | null;
  selectedFeature: GeoJSONFeature | null;
  onSelectFeature: (feature: GeoJSONFeature) => void;
  isQueueOpen?: boolean;
  onToggleQueue?: () => void;
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
  isQueueOpen = true,
  onToggleQueue,
}) => {
  // Layer visibility toggles (QGIS layer panel style)
  const [showCadastral, setShowCadastral] = useState(true);
  const [showMunicipal, setShowMunicipal] = useState(true);
  const [showStructures, setShowStructures] = useState(true);
  const [layerPanelOpen, setLayerPanelOpen] = useState(false);

  // Synthetic dataset center coordinates (around [0.001, 76.51] WGS84)
  const defaultCenter: [number, number] = [0.001, 76.513];

  // Cadastral styling
  const cadastralStyle = (feature: any) => {
    const isSelected =
      selectedFeature?.properties?.parcel_id === feature?.properties?.parcel_id;
    return {
      color: isSelected ? '#29cc39' : '#4f46e5',
      weight: isSelected ? 3.5 : 1.5,
      opacity: 0.9,
      fillColor: isSelected ? '#29cc39' : '#4f46e5',
      fillOpacity: isSelected ? 0.15 : 0.05,
      dashArray: '4, 4',
    };
  };

  // Municipal building styling
  const municipalStyle = () => ({
    color: '#64748b',
    weight: 1.5,
    opacity: 0.8,
    fillColor: '#cbd5e1',
    fillOpacity: 0.1,
  });

  // Review structure styling (Outlined shapefile rendering per §5 requirement)
  const structureStyle = (feature: any) => {
    const props: StructureProperties = feature?.properties || {};
    const isSelected =
      selectedFeature?.properties?.structure_id === props.structure_id;

    let color = '#29cc39'; // verified green
    if (props.status === 'audit_pending') {
      color = '#d97706'; // amber
    } else if (props.status === 'disputed') {
      color = '#dc2626'; // red
    } else if (props.status === 'locked_disputed') {
      color = '#7c3aed'; // purple
    }

    return {
      color: isSelected ? '#22a229' : color,
      weight: isSelected ? 4 : 2.5,
      opacity: 1.0,
      fillColor: color,
      fillOpacity: 0, // Pure outline with NO fill per user requirement
    };
  };

  return (
    <div className="relative flex-1 h-full w-full bg-[#efefea] overflow-hidden">
      {/* Floating Toggle Button when Queue Sidebar is Closed */}
      {!isQueueOpen && onToggleQueue && (
        <button
          onClick={onToggleQueue}
          title="Open Review Queue Sidebar"
          className="absolute top-4 left-4 z-20 flex items-center gap-2 bg-[#fafaf7] hover:bg-white text-slate-800 px-3.5 py-2 rounded-xl border border-[#d2d2c8] shadow-lg text-xs font-bold transition cursor-pointer"
        >
          <Menu className="w-4 h-4 text-[#29cc39]" />
          <span>Open Review Queue</span>
        </button>
      )}

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
                { className: 'bg-slate-900 text-white text-xs border border-slate-700 shadow-md', sticky: true }
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
                { className: 'bg-slate-900 text-white text-xs border border-slate-700 shadow-md', sticky: true }
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
                { className: 'bg-slate-900 text-white text-xs border border-slate-700 shadow-md', sticky: true }
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
          className="flex items-center gap-2 bg-[#fafaf7] hover:bg-white text-slate-800 px-3.5 py-2 rounded-xl border border-[#d2d2c8] shadow-lg text-xs font-bold transition cursor-pointer"
        >
          <Layers className="w-4 h-4 text-[#29cc39]" />
          <span>GIS Layers</span>
        </button>

        {layerPanelOpen && (
          <div className="mt-2 w-64 bg-[#fafaf7] border border-[#d2d2c8] rounded-xl p-3.5 shadow-2xl backdrop-blur text-xs space-y-3">
            <div className="flex items-center justify-between border-b border-[#e0e0d6] pb-2 font-black text-slate-800">
              <span>Layer Visibility</span>
              <span className="text-[10px] text-slate-500 font-semibold uppercase">Toggle ON/OFF</span>
            </div>

            {/* Cadastral Layer Toggle */}
            <label className="flex items-center justify-between cursor-pointer group">
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded border border-indigo-500 bg-indigo-100"></span>
                <span className="text-slate-700 font-semibold group-hover:text-slate-900">Cadastral Parcels</span>
              </div>
              <button
                onClick={() => setShowCadastral(!showCadastral)}
                className="text-slate-500 hover:text-slate-800 cursor-pointer"
              >
                {showCadastral ? <Eye className="w-4 h-4 text-indigo-600" /> : <EyeOff className="w-4 h-4 text-slate-400" />}
              </button>
            </label>

            {/* Municipal Layer Toggle */}
            <label className="flex items-center justify-between cursor-pointer group">
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded border border-slate-400 bg-slate-200"></span>
                <span className="text-slate-700 font-semibold group-hover:text-slate-900">Municipal Records</span>
              </div>
              <button
                onClick={() => setShowMunicipal(!showMunicipal)}
                className="text-slate-500 hover:text-slate-800 cursor-pointer"
              >
                {showMunicipal ? <Eye className="w-4 h-4 text-slate-700" /> : <EyeOff className="w-4 h-4 text-slate-400" />}
              </button>
            </label>

            {/* Review Structures Layer Toggle */}
            <label className="flex items-center justify-between cursor-pointer group">
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded border border-[#29cc39] bg-[#29cc39]/20"></span>
                <span className="text-slate-700 font-semibold group-hover:text-slate-900">Physical Structures</span>
              </div>
              <button
                onClick={() => setShowStructures(!showStructures)}
                className="text-slate-500 hover:text-slate-800 cursor-pointer"
              >
                {showStructures ? <Eye className="w-4 h-4 text-[#29cc39]" /> : <EyeOff className="w-4 h-4 text-slate-400" />}
              </button>
            </label>

            {/* Map Legend */}
            <div className="border-t border-[#e0e0d6] pt-2 space-y-1 text-[11px] text-slate-600">
              <div className="font-bold text-slate-800 mb-1">Status Legend (Outlines)</div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#29cc39]"></span>
                <span>Verified (GeoAI / Lekhpal)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                <span>Audit Pending (&gt;10m)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-600"></span>
                <span>Disputed (&gt;20m / Multi-parcel)</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Floating Feature Inspector Drawer */}
      {selectedFeature && (
        <div className="absolute bottom-4 left-4 right-4 max-w-xl mx-auto z-20 bg-[#fafaf7] border border-[#29cc39] rounded-2xl p-4 shadow-2xl text-xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-[#29cc39]" />
              <span className="font-extrabold text-slate-900">
                {selectedFeature.properties?.structure_id
                  ? `Structure Inspector: ${selectedFeature.properties.structure_id}`
                  : `Cadastral Parcel: ${selectedFeature.properties.parcel_id}`}
              </span>
            </div>
            <span className="text-[10px] bg-[#29cc39]/15 border border-[#29cc39]/30 text-[#1b7a21] font-bold px-2 py-0.5 rounded-md uppercase">
              {selectedFeature.properties?.status || 'Cadastral Parcel'}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 bg-[#f4f4ef] p-2.5 rounded-xl border border-[#e0e0d6] text-[11px]">
            <div>
              <span className="text-slate-400 block text-[10px]">Assigned Tehsil:</span>
              <span className="text-slate-800 font-bold">
                {selectedFeature.properties?.cadastral_record?.tehsil ||
                  selectedFeature.properties?.tehsil ||
                  'N/A'}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Khasra / Khata:</span>
              <span className="text-slate-800 font-bold">
                {selectedFeature.properties?.cadastral_record?.khasra_no ||
                  selectedFeature.properties?.khasra_no ||
                  'N/A'}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Overflow / Area:</span>
              <span className="text-amber-700 font-extrabold">
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
