import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listClusters, getClusterCapacity } from '@/api/clusters'
import { listNodes } from '@/api/nodes'
import { listWorkloads } from '@/api/workloads'
import { getClusterAggregate } from '@/api/telemetry'
import { MetricCard } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import {
  DraggableWidgetGrid,
  DashboardWidgetConfig,
} from '@/components/dashboard/DraggableWidgetGrid'
import {
  ClusterCapacityWidget,
  FleetInventoryWidget,
  WorkloadOperationsWidget,
  TelemetryObservabilityWidget,
  BackendHealthWidget,
  MlRegistrySummaryWidget,
} from '@/components/dashboard/DashboardWidgets'
import {
  Layers,
  Server,
  Cpu,
  CheckCircle2,
  ShieldAlert,
  HeartPulse,
  Activity,
  Plus,
  Brain,
} from 'lucide-react'

export function DashboardPage() {
  const navigate = useNavigate()
  const [selectedClusterId, setSelectedClusterId] = useState<string>('')

  // 1. Clusters query
  const {
    data: clusters = [],
    isLoading: isClustersLoading,
    error: clustersError,
    refetch: refetchClusters,
  } = useQuery({
    queryKey: ['clusters'],
    queryFn: ({ signal }) => listClusters({ limit: 100 }, signal),
  })

  // Select first cluster automatically if none explicitly chosen
  const activeClusterId = selectedClusterId || (clusters.length > 0 ? clusters[0].id : '')
  const activeCluster = clusters.find((c) => c.id === activeClusterId)

  // 2. Nodes query
  const {
    data: nodes = [],
    isLoading: isNodesLoading,
    error: nodesError,
    refetch: refetchNodes,
  } = useQuery({
    queryKey: ['nodes'],
    queryFn: ({ signal }) => listNodes({ limit: 200 }, signal),
  })

  // 3. Workloads query
  const {
    data: workloads = [],
    isLoading: isWorkloadsLoading,
    error: workloadsError,
    refetch: refetchWorkloads,
  } = useQuery({
    queryKey: ['workloads'],
    queryFn: ({ signal }) => listWorkloads({ limit: 200 }, signal),
  })

  // 4. Cluster Capacity query (for selected cluster)
  const {
    data: capacity,
    isLoading: isCapacityLoading,
    error: capacityError,
    refetch: refetchCapacity,
  } = useQuery({
    queryKey: ['cluster-capacity', activeClusterId],
    queryFn: ({ signal }) => getClusterCapacity(activeClusterId, signal),
    enabled: !!activeClusterId,
  })

  // 5. Cluster Aggregate Telemetry query (for selected cluster)
  const {
    data: aggregate,
    isLoading: isAggregateLoading,
    refetch: refetchAggregate,
  } = useQuery({
    queryKey: ['cluster-aggregate', activeClusterId],
    queryFn: ({ signal }) => getClusterAggregate(activeClusterId, signal),
    enabled: !!activeClusterId,
    refetchInterval: 15000,
  })

  // Aggregate Calculations strictly from API responses
  const totalNodesCount = nodes.length
  const readyNodesCount = nodes.filter((n) => n.status === 'READY').length
  const cordonedNodesCount = nodes.filter((n) => n.is_cordoned).length

  const fleetMeanHealthScore =
    totalNodesCount > 0
      ? (nodes.reduce((acc, n) => acc + n.health_score, 0) / totalNodesCount).toFixed(1)
      : null

  const activeWorkloadCount = workloads.filter(
    (w) => w.status === 'RUNNING' || w.status === 'SCHEDULED'
  ).length
  const pendingWorkloadCount = workloads.filter((w) => w.status === 'PENDING').length

  const anyError = clustersError || nodesError || workloadsError
  const hasNoData = !isClustersLoading && clusters.length === 0 && nodes.length === 0

  // 6 Candidate Dashboard Widgets Config
  const defaultWidgets: DashboardWidgetConfig[] = [
    {
      id: 'cluster-overview',
      title: 'Cluster Overview & Capacity',
      icon: <Layers className="w-4 h-4" />,
      colSpan: 'col-span-1 md:col-span-2',
      component: (
        <ClusterCapacityWidget
          clusters={clusters}
          activeClusterId={activeClusterId}
          onSelectCluster={setSelectedClusterId}
          isClustersLoading={isClustersLoading}
          capacity={capacity}
          isCapacityLoading={isCapacityLoading}
          capacityError={capacityError}
          refetchCapacity={refetchCapacity}
        />
      ),
    },
    {
      id: 'fleet-inventory',
      title: 'Compute Fleet Inventory',
      icon: <Server className="w-4 h-4" />,
      colSpan: 'col-span-1',
      component: (
        <FleetInventoryWidget
          nodes={nodes}
          isNodesLoading={isNodesLoading}
        />
      ),
    },
    {
      id: 'workload-operations',
      title: 'Workload Operations',
      icon: <Cpu className="w-4 h-4" />,
      colSpan: 'col-span-1',
      component: (
        <WorkloadOperationsWidget
          workloads={workloads}
          isWorkloadsLoading={isWorkloadsLoading}
        />
      ),
    },
    {
      id: 'telemetry-observability',
      title: 'Real-Time Telemetry Observability',
      icon: <Activity className="w-4 h-4" />,
      colSpan: 'col-span-1 md:col-span-2',
      component: (
        <TelemetryObservabilityWidget
          activeClusterId={activeClusterId}
          activeClusterName={activeCluster?.name}
          aggregate={aggregate}
          isAggregateLoading={isAggregateLoading}
          refetchAggregate={refetchAggregate}
        />
      ),
    },
    {
      id: 'backend-health',
      title: 'System & Engine Health',
      icon: <HeartPulse className="w-4 h-4" />,
      colSpan: 'col-span-1',
      component: <BackendHealthWidget />,
    },
    {
      id: 'ml-registry-summary',
      title: 'Machine Learning Model Catalog',
      ariaLabel: 'Scientific ML Model Registry',
      icon: <Brain className="w-4 h-4" />,
      colSpan: 'col-span-1 md:col-span-2 xl:col-span-3',
      component: <MlRegistrySummaryWidget />,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Any API Error Banner */}
      {anyError && (
        <ErrorState
          title="Telemetry Ingestion Warning"
          message={
            anyError instanceof Error
              ? anyError.message
              : 'Failed to retrieve telemetry data from one or more backend endpoints.'
          }
          onRetry={() => {
            refetchClusters()
            refetchNodes()
            refetchWorkloads()
          }}
        />
      )}

      {/* Top Fleet Metric Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3.5">
        <MetricCard
          label="Total Clusters"
          value={isClustersLoading ? '—' : clusters.length}
          subtext={clusters.length >= 100 ? 'Queried page limit (100)' : 'Active namespaces'}
          icon={<Layers className="w-4 h-4" />}
          variant="cyan"
        />
        <MetricCard
          label="Total Nodes"
          value={isNodesLoading ? '—' : totalNodesCount}
          subtext={nodes.length >= 200 ? 'Queried page limit (200)' : 'Managed hardware units'}
          icon={<Server className="w-4 h-4" />}
          variant="default"
        />
        <MetricCard
          label="Ready Nodes"
          value={isNodesLoading ? '—' : readyNodesCount}
          subtext={
            totalNodesCount > 0
              ? `${Math.round((readyNodesCount / totalNodesCount) * 100)}% available for placement`
              : 'No nodes registered'
          }
          icon={<CheckCircle2 className="w-4 h-4" />}
          variant="success"
        />
        <MetricCard
          label="Cordoned Nodes"
          value={isNodesLoading ? '—' : cordonedNodesCount}
          subtext="Excluded from scheduler"
          icon={<ShieldAlert className="w-4 h-4" />}
          variant={cordonedNodesCount > 0 ? 'warning' : 'default'}
        />
        <MetricCard
          label="Mean Fleet Health"
          value={isNodesLoading ? '—' : fleetMeanHealthScore !== null ? `${fleetMeanHealthScore}/100` : '—'}
          subtext="Deterministic heuristic score"
          icon={<HeartPulse className="w-4 h-4" />}
          variant={
            fleetMeanHealthScore && parseFloat(fleetMeanHealthScore) < 50
              ? 'critical'
              : 'default'
          }
        />
        <MetricCard
          label="Active Workloads"
          value={isWorkloadsLoading ? '—' : activeWorkloadCount}
          subtext={`${pendingWorkloadCount} pending in queue`}
          icon={<Cpu className="w-4 h-4" />}
          variant="cyan"
        />
      </div>

      {/* Intentional Empty State if database has no clusters */}
      {hasNoData && (
        <EmptyState
          title="No Clusters or Compute Nodes Registered"
          description="The IntelliCluster database is currently unpopulated. Initialize a cluster and register nodes to start ingesting telemetry and scheduling workloads."
          action={{
            label: 'Create First Cluster',
            icon: <Plus className="w-4 h-4" />,
            onClick: () => navigate('/clusters'),
          }}
        />
      )}

      {/* Draggable Dashboard Widget Grid with Animated Rearrangement */}
      <DraggableWidgetGrid initialWidgets={defaultWidgets} />
    </div>
  )
}
