import { useEffect, useState, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { VerificationQueue } from './components/VerificationQueue';
import { GISMap } from './components/GISMap';
import { ConsolidatedParcelsView } from './components/ConsolidatedParcelsView';
import { AuditLogModal } from './components/AuditLogModal';
import { LoginPage } from './components/LoginPage';
import { SignupPage } from './components/SignupPage';
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
    username: 'ramesh_alpha',
    name: 'Ramesh Kumar',
    role: 'Lekhpal',
    tehsil: 'Tehsil-Alpha',
    district: 'Kumaon District',
  },
  official_beta: {
    official_id: 'official_beta',
    username: 'suresh_beta',
    name: 'Suresh Singh',
    role: 'Lekhpal',
    tehsil: 'Tehsil-Beta',
    district: 'Kumaon District',
  },
  revenue_alpha: {
    official_id: 'revenue_alpha',
    username: 'revenue_alpha',
    name: 'Vikram Sharma',
    role: 'Revenue Inspector',
    tehsil: 'Tehsil-Alpha',
    district: 'Kumaon District',
  },
  tehsildar_alpha: {
    official_id: 'tehsildar_alpha',
    username: 'tehsildar_alpha',
    name: 'Dr. Anita Verma',
    role: 'Tehsildar',
    tehsil: 'Tehsil-Alpha',
    district: 'Kumaon District',
  },
  revenue_beta: {
    official_id: 'revenue_beta',
    username: 'revenue_beta',
    name: 'mahesh Sharma',
    role: 'Revenue Inspector',
    tehsil: 'Tehsil-Beta',
    district: 'Kumaon District',
  },
  tehsildar_beta: {
    official_id: 'tehsildar_beta',
    username: 'tehsildar_beta',
    name: 'Mr Avinash gupta',
    role: 'Tehsildar',
    tehsil: 'Tehsil-Beta',
    district: 'Kumaon District',
  },
};

export default function App() {
  // Authentication & Auth Routing state
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return localStorage.getItem('gis_autopilot_auth') === 'true';
  });
  const [authPageMode, setAuthPageMode] = useState<'login' | 'signup'>('login');
  const [currentOfficial, setCurrentOfficial] = useState<OfficialProfile>(() => {
    const saved = localStorage.getItem('gis_autopilot_official');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {}
    }
    return INITIAL_OFFICIALS.official_alpha;
  });
  

  // Navigation & Sidebar Toggle state
  const [activeView, setActiveView] = useState<'queue' | 'parcels'>('queue');
  const [isQueueOpen, setIsQueueOpen] = useState<boolean>(true);

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
      console.log(data.official_id,"\n",queue)
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
  // Load Audit Trail Log (§18 — Tehsil-Scoped)
  // -------------------------------------------------------------------------
  const loadAuditLog = useCallback(async () => {
    setIsAuditLoading(true);
    try {
      const data = await api.fetchAuditLog(currentOfficial.official_id);
      setAuditLog(data.entries || []);
    } catch (err) {
      console.error('Error loading audit trail:', err);
    } finally {
      setIsAuditLoading(false);
    }
  }, [currentOfficial.official_id]);

  // Initial mount load when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadBaseLayers();
      loadQueue(currentOfficial.official_id);
      loadParcels();
    }
  }, [isAuthenticated, loadBaseLayers, loadQueue, loadParcels, currentOfficial.official_id]);

  // Handle Login
  const handleLogin = (official: OfficialProfile) => {
    setCurrentOfficial(official);
    setIsAuthenticated(true);
    localStorage.setItem('gis_autopilot_auth', 'true');
    localStorage.setItem('gis_autopilot_official', JSON.stringify(official));
  };

  // Handle Logout
  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('gis_autopilot_auth');
    localStorage.removeItem('gis_autopilot_official');
    setSelectedFeature(null);
  };

  // Handle switching official profile inside active workspace
  const handleSwitchOfficial = (officialId: string) => {
    const nextOfficial = INITIAL_OFFICIALS[officialId] || currentOfficial;
    setCurrentOfficial(nextOfficial);
    localStorage.setItem('gis_autopilot_official', JSON.stringify(nextOfficial));
    loadQueue(nextOfficial.official_id);
    setSelectedFeature(null);
  };

  // -------------------------------------------------------------------------
  // Handle Human Decision Action (§8 — 3-Layer Workflow)
  // -------------------------------------------------------------------------
  const handleHumanAction = async (
    structureId: string,
    action: 'mark_verified' | 'lock_disputed' | 'forward_to_revenue' | 'forward_to_tehsildar' | 'tehsildar_commit',
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

  // If not authenticated, render Login or Signup page
  if (!isAuthenticated) {
    if (authPageMode === 'signup') {
      return <SignupPage onNavigateToLogin={() => setAuthPageMode('login')} />;
    }
    return (
      <LoginPage
        onLogin={handleLogin}
        onNavigateToSignup={() => setAuthPageMode('signup')}
      />
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#f4f4ef]">
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
        onLogout={handleLogout}
        isQueueOpen={isQueueOpen}
        onToggleQueue={() => setIsQueueOpen(!isQueueOpen)}
      />

      {/* Main Content Workspace */}
      <main className="flex-1 flex overflow-hidden relative">
        {activeView === 'queue' ? (
          <>
            {/* Left Sidebar: Lekhpal Review Queue (Toggleable via Hamburger Button) */}
            {isQueueOpen && (
              <VerificationQueue
                queue={queue}
                selectedStructureId={selectedFeature?.properties?.structure_id || null}
                onSelectStructure={(feature) => setSelectedFeature(feature)}
                onAction={handleHumanAction}
                currentTehsil={currentOfficial.tehsil}
                officialRole={currentOfficial.role}
                isLoading={isQueueLoading}
                onCloseQueue={() => setIsQueueOpen(false)}
              />
            )}

            {/* Center/Right Workspace: Interactive Map */}
            <GISMap
              cadastralLayer={cadastralLayer}
              municipalLayer={municipalLayer}
              reviewStructuresLayer={reviewStructuresLayer}
              selectedFeature={selectedFeature}
              onSelectFeature={(feature) => setSelectedFeature(feature)}
              isQueueOpen={isQueueOpen}
              onToggleQueue={() => setIsQueueOpen(!isQueueOpen)}
            />
          </>
        ) : (
          /* Single Source of Truth View: Stage 4 Consolidated Parcels */
          <ConsolidatedParcelsView
            currentOfficial={currentOfficial}
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
