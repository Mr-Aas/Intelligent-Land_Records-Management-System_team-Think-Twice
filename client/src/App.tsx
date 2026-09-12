import { useEffect, useState, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { VerificationQueue } from './components/VerificationQueue';
import { GISMap } from './components/GISMap';
import { ConsolidatedParcelsView } from './components/ConsolidatedParcelsView';
import { AuditLogModal } from './components/AuditLogModal';
import type {
  AuditLogEntry,
  ConsolidatedParcel,
  GeoJSONFeature,
  GeoJSONFeatureCollection,
  OfficialProfile,
  StructureProperties,
} from './types';
import * as api from './services/api';

// Synthetic official profiles (§8)
const INITIAL_OFFICIALS: Record<string, OfficialProfile> = {
  official_alpha: {
    official_id: 'official_alpha',
    username: 'official_alpha',
    name: 'Ramesh Kumar',
    role: 'Lekhpal',
    tehsil: 'Tehsil-Alpha',
    district: 'Synthetic-District',
  },
  official_beta: {
    official_id: 'official_beta',
    username: 'official_beta',
    name: 'Suresh Singh',
    role: 'Lekhpal',
    tehsil: 'Tehsil-Beta',
    district: 'Synthetic-District',
  },
};

export default function App() {
  // Navigation & Authentication state
  const [activeView, setActiveView] = useState<'queue' | 'parcels'>('queue');
  const [currentOfficial, setCurrentOfficial] = useState<OfficialProfile>(
    INITIAL_OFFICIALS.official_beta
  );

  // GIS Layers state
  const [cadastralLayer, setCadastralLayer] = useState<GeoJSONFeatureCollection | null>(null);
  const [municipalLayer, setMunicipalLayer] = useState<GeoJSONFeatureCollection | null>(null);
  const [reviewStructuresLayer, setReviewStructuresLayer] = useState<GeoJSONFeatureCollection<StructureProperties> | null>(null);

  // Workflow queue & selection state
  const [queue, setQueue] = useState<Array<GeoJSONFeature<StructureProperties>>>([]);
  const [selectedFeature, setSelectedFeature] = useState<GeoJSONFeature | null>(null);
  const [isQueueLoading, setIsQueueLoading] = useState(false);

  // Stage 4 consolidated parcels state
  const [parcels, setParcels] = useState<ConsolidatedParcel[]>([]);
  const [selectedParcelId, setSelectedParcelId] = useState<string | null>(null);
  const [isStage4Running, setIsStage4Running] = useState(false);

  // Audit log modal state
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);
  const [isAuditLoading, setIsAuditLoading] = useState(false);

  // -------------------------------------------------------------------------
  // Load Base GIS Layers (Cadastral & Municipal)
  // -------------------------------------------------------------------------
  const loadBaseLayers = useCallback(async () => {
    try {
      const [cad, mun, rev] = await Promise.all([
        api.fetchLayer('cadastral'),
        api.fetchLayer('municipal'),
        api.fetchLayer('review-structures'),
      ]);
      setCadastralLayer(cad);
      setMunicipalLayer(mun);
      setReviewStructuresLayer(rev as any);
    } catch (err) {
      console.error('Error loading base GIS layers:', err);
    }
  }, []);

  // -------------------------------------------------------------------------
  // Load Verification Queue for Active Official's Tehsil (§8)
  // -------------------------------------------------------------------------
  const loadQueue = useCallback(async (officialId: string) => {
    setIsQueueLoading(true);
    try {
      const data = await api.fetchVerificationQueue(officialId);
      setQueue(data.features || []);
    } catch (err) {
      console.error('Error loading verification queue:', err);
    } finally {
      setIsQueueLoading(false);
    }
  }, []);

  // -------------------------------------------------------------------------
  // Load Stage 4 Consolidated Parcels (§10)
  // -------------------------------------------------------------------------
  const loadParcels = useCallback(async () => {
    try {
      const data = await api.fetchConsolidatedParcels();
      setParcels(data.parcels || []);
      if (data.parcels && data.parcels.length > 0 && !selectedParcelId) {
        setSelectedParcelId(data.parcels[0].parcel_id);
      }
    } catch (err) {
      console.error('Error loading consolidated parcels:', err);
    }
  }, [selectedParcelId]);

  // -------------------------------------------------------------------------
  // Load Audit Trail Log (§18)
  // -------------------------------------------------------------------------
  const loadAuditLog = useCallback(async () => {
    setIsAuditLoading(true);
    try {
      const data = await api.fetchAuditLog();
      setAuditLog(data.entries || []);
    } catch (err) {
      console.error('Error loading audit trail:', err);
    } finally {
      setIsAuditLoading(false);
    }
  }, []);

  // Initial mount load
  useEffect(() => {
    loadBaseLayers();
    loadQueue(currentOfficial.official_id);
    loadParcels();
  }, [loadBaseLayers, loadQueue, loadParcels, currentOfficial.official_id]);

  // Handle switching official profile
  const handleSwitchOfficial = (officialId: string) => {
    const nextOfficial = INITIAL_OFFICIALS[officialId];
    if (nextOfficial) {
      setCurrentOfficial(nextOfficial);
      loadQueue(nextOfficial.official_id);
      setSelectedFeature(null);
    }
  };

  // -------------------------------------------------------------------------
  // Handle Human Decision Action (§8 — Mark Verified / Lock Disputed)
  // -------------------------------------------------------------------------
  const handleHumanAction = async (
    structureId: string,
    action: 'mark_verified' | 'lock_disputed',
    notes: string
  ) => {
    await api.submitHumanAction(structureId, currentOfficial.official_id, action, notes);

    // Refresh queue & review layer
    await Promise.all([
      loadQueue(currentOfficial.official_id),
      api.fetchLayer('review-structures').then((rev) =>
        setReviewStructuresLayer(rev as any)
      ),
      loadAuditLog(),
    ]);

    // Clear or update selected feature
    setSelectedFeature(null);
  };

  // -------------------------------------------------------------------------
  // Handle Triggering Stage 4 Consolidation (§9, §10)
  // -------------------------------------------------------------------------
  const handleTriggerStage4 = async () => {
    setIsStage4Running(true);
    try {
      await api.triggerStage4();
      await loadParcels();
    } catch (err) {
      console.error('Error triggering Stage 4:', err);
    } finally {
      setIsStage4Running(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950">
      {/* Top Application Navbar */}
      <Navbar
        currentOfficial={currentOfficial}
        onSwitchOfficial={handleSwitchOfficial}
        activeView={activeView}
        onSelectView={setActiveView}
        onOpenAuditLog={() => {
          loadAuditLog();
          setIsAuditModalOpen(true);
        }}
        onTriggerStage4={handleTriggerStage4}
        isStage4Running={isStage4Running}
        pendingCount={queue.length}
      />

      {/* Main Content Workspace */}
      <main className="flex-1 flex overflow-hidden relative">
        {activeView === 'queue' ? (
          <>
            {/* Left Sidebar: Lekhpal Review Queue */}
            <VerificationQueue
              queue={queue}
              selectedStructureId={selectedFeature?.properties?.structure_id || null}
              onSelectStructure={(feature) => setSelectedFeature(feature)}
              onAction={handleHumanAction}
              currentTehsil={currentOfficial.tehsil}
              isLoading={isQueueLoading}
            />

            {/* Center/Right Workspace: Interactive QGIS-like Map */}
            <GISMap
              cadastralLayer={cadastralLayer}
              municipalLayer={municipalLayer}
              reviewStructuresLayer={reviewStructuresLayer}
              selectedFeature={selectedFeature}
              onSelectFeature={(feature) => setSelectedFeature(feature)}
            />
          </>
        ) : (
          /* Single Source of Truth View: Stage 4 Consolidated Parcels */
          <ConsolidatedParcelsView
            parcels={parcels}
            selectedParcelId={selectedParcelId}
            onSelectParcel={(id) => setSelectedParcelId(id)}
            onTriggerStage4={handleTriggerStage4}
            isStage4Running={isStage4Running}
          />
        )}
      </main>

      {/* Audit Log Timeline Modal */}
      <AuditLogModal
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        entries={auditLog}
        onRefresh={loadAuditLog}
        isLoading={isAuditLoading}
      />
    </div>
  );
}
