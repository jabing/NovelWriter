<template>
  <div class="graph-visualization">
    <!-- Loading State -->
    <div v-if="loading" class="graph-loading" role="status" aria-live="polite">
      <div class="loading-spinner" aria-hidden="true"></div>
      <span class="loading-text">Loading graph...</span>
    </div>

    <!-- Empty State -->
    <div v-else-if="!hasData" class="graph-empty" role="status" aria-live="polite">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 16v-4M12 8h.01"/>
      </svg>
      <h3 class="empty-title">No Graph Data</h3>
      <p class="empty-description">Add characters and relationships to visualize the connection graph.</p>
    </div>

    <!-- Graph Container -->
    <div v-else class="graph-container">
      <!-- Controls -->
      <div class="graph-controls" role="toolbar" aria-label="Graph controls">
        <button
          class="control-btn"
          @click="zoomIn"
          aria-label="Zoom in"
          title="Zoom in"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
            <path d="M11 8v6M8 11h6"/>
          </svg>
        </button>
        <button
          class="control-btn"
          @click="zoomOut"
          aria-label="Zoom out"
          title="Zoom out"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
            <path d="M8 11h6"/>
          </svg>
        </button>
        <button
          class="control-btn"
          @click="resetView"
          aria-label="Reset view"
          title="Reset view"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 12"/>
            <path d="M3 3v9h9"/>
          </svg>
        </button>
      </div>

      <!-- Legend -->
      <div class="graph-legend" role="region" aria-label="Relationship type legend">
        <div class="legend-title">Relationship Types</div>
        <div class="legend-items">
          <div
            v-for="(color, type) in relationshipColors"
            :key="type"
            class="legend-item"
          >
            <span class="legend-color" :style="{ backgroundColor: color }" aria-hidden="true"></span>
            <span class="legend-label">{{ formatRelationshipType(type) }}</span>
          </div>
        </div>
      </div>

      <!-- ECharts Graph -->
      <v-chart
        ref="chartRef"
        :options="chartOptions"
        autoresize
        class="echarts-graph"
        @click="handleChartClick"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import * as echarts from 'echarts';
import VChart from 'vue-echarts';

// Types
interface GraphNode {
  data: {
    id: string;
    label: string;
    type?: string;
    properties?: {
      aliases?: string[];
      tier?: number;
      bio?: string;
      status?: string;
    };
  };
}

interface GraphEdge {
  data: {
    source: string;
    target: string;
    relationship?: string;
    properties?: {
      strength?: number;
      description?: string;
    };
  };
}

// Props
const props = defineProps<{
  nodes: GraphNode[];
  edges: GraphEdge[];
  loading?: boolean;
}>();

// Emits
const emit = defineEmits<{
  (e: 'node-click', node: GraphNode['data']): void;
  (e: 'edge-click', edge: GraphEdge['data']): void;
}>();

// Refs
const chartRef = ref<InstanceType<typeof VChart> | null>(null);

// Relationship colors mapping
const relationshipColors: Record<string, string> = {
  FAMILY: '#FF6B6B',
  FRIEND: '#4ECDC4',
  ENEMY: '#E74C3C',
  ALLY: '#27AE60',
  ROMANTIC: '#E91E63',
  MENTOR: '#9B59B6',
  STUDENT: '#3498DB',
  RIVAL: '#F39C12',
  BUSINESS: '#95A5A6',
  DEFAULT: '#007AFF'
};

// Computed
const hasData = computed(() => props.nodes.length > 0);

// Transform nodes for ECharts
const transformNodes = computed(() => {
  return props.nodes.map((node) => {
    const tier = node.data.properties?.tier ?? 1;
    const nodeSize = 20 + tier * 8; // Larger nodes for higher tier characters

    return {
      id: node.data.id,
      name: node.data.label,
      value: tier,
      symbolSize: nodeSize,
      category: node.data.type || 'character',
      // Store original data for click events
      originalData: node.data,
      label: {
        show: true,
        formatter: '{b}',
        fontSize: 12,
        color: 'var(--color-text-primary)'
      },
      itemStyle: {
        color: getNodeColor(node.data),
        borderColor: '#fff',
        borderWidth: 2,
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.2)'
      },
      emphasis: {
        scale: 1.2,
        itemStyle: {
          shadowBlur: 20,
          shadowColor: 'rgba(0, 0, 0, 0.3)'
        }
      }
    };
  });
});

// Transform edges for ECharts
const transformEdges = computed(() => {
  return props.edges.map((edge) => {
    const relationship = edge.data.relationship || 'DEFAULT';
    const strength = edge.data.properties?.strength ?? 0.5;
    const lineWidth = 1 + strength * 4; // Thicker lines for stronger relationships

    return {
      source: edge.data.source,
      target: edge.data.target,
      value: strength,
      // Store original data for click events
      originalData: edge.data,
      lineStyle: {
        color: relationshipColors[relationship] || relationshipColors.DEFAULT,
        width: lineWidth,
        curveness: 0.2,
        opacity: 0.8
      },
      label: {
        show: false,
        formatter: relationship
      },
      emphasis: {
        lineStyle: {
          width: lineWidth + 2,
          opacity: 1
        }
      }
    };
  });
});

// Chart options
const chartOptions = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item',
    backgroundColor: 'var(--color-surface)',
    borderColor: 'var(--color-border)',
    borderWidth: 1,
    textStyle: {
      color: 'var(--color-text-primary)'
    },
    formatter: (params: any) => {
      if (params.dataType === 'node') {
        return formatNodeTooltip(params.data);
      } else if (params.dataType === 'edge') {
        return formatEdgeTooltip(params.data);
      }
      return '';
    }
  },
  animationDuration: 1500,
  animationEasingUpdate: 'quinticInOut',
  series: [
    {
      type: 'graph',
      layout: 'force',
      data: transformNodes.value,
      links: transformEdges.value,
      roam: true, // Enable zoom and pan
      draggable: true,
      focusNodeAdjacency: true,
      force: {
        repulsion: 1000,
        gravity: 0.1,
        edgeLength: [100, 200],
        layoutAnimation: true
      },
      lineStyle: {
        curveness: 0.2
      },
      label: {
        show: true,
        position: 'bottom',
        formatter: '{b}'
      },
      edgeLabel: {
        show: false
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      }
    }
  ]
}));

// Helper functions
function getNodeColor(nodeData: GraphNode['data']): string {
  const status = nodeData.properties?.status;
  switch (status) {
    case 'deceased':
      return '#95A5A6'; // Gray for deceased
    case 'missing':
      return '#F39C12'; // Orange for missing
    case 'unknown':
      return '#9B59B6'; // Purple for unknown
    default:
      return '#007AFF'; // Primary blue for alive/default
  }
}

function formatNodeTooltip(data: any): string {
  const nodeData = data.originalData;
  const tier = nodeData.properties?.tier ?? 1;
  const status = nodeData.properties?.status || 'alive';
  const aliases = nodeData.properties?.aliases?.slice(0, 3).join(', ') || '';

  let html = `<div class="tooltip-content">`;
  html += `<div class="tooltip-title">${nodeData.label}</div>`;
  html += `<div class="tooltip-type">${nodeData.type || 'Character'} • Tier ${tier}</div>`;
  html += `<div class="tooltip-status" style="color: ${getStatusColor(status)}">Status: ${status}</div>`;

  if (aliases) {
    html += `<div class="tooltip-aliases">Also known as: ${aliases}</div>`;
  }

  if (nodeData.properties?.bio) {
    const bio = nodeData.properties.bio.substring(0, 100);
    html += `<div class="tooltip-bio">${bio}${nodeData.properties.bio.length > 100 ? '...' : ''}</div>`;
  }

  html += `</div>`;
  return html;
}

function formatEdgeTooltip(data: any): string {
  const edgeData = data.originalData;
  const relationship = edgeData.relationship || 'Relationship';
  const strength = edgeData.properties?.strength ?? 0.5;
  const strengthPercent = Math.round(strength * 100);
  const description = edgeData.properties?.description || '';

  let html = `<div class="tooltip-content">`;
  html += `<div class="tooltip-title">${relationship}</div>`;
  html += `<div class="tooltip-strength">Strength: ${strengthPercent}%</div>`;

  if (description) {
    html += `<div class="tooltip-description">${description}</div>`;
  }

  html += `</div>`;
  return html;
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'deceased':
      return '#E74C3C';
    case 'missing':
      return '#F39C12';
    case 'unknown':
      return '#9B59B6';
    default:
      return '#27AE60';
  }
}

function formatRelationshipType(type: string): string {
  return type.charAt(0).toUpperCase() + type.slice(1).toLowerCase();
}

// Event handlers
function handleChartClick(params: any) {
  if (params.dataType === 'node') {
    emit('node-click', params.data.originalData);
  } else if (params.dataType === 'edge') {
    emit('edge-click', params.data.originalData);
  }
}

// Zoom controls
function zoomIn() {
  const chart = chartRef.value?.chart;
  if (chart) {
    const currentZoom = chart.getOption()?.series?.[0]?.zoom || 1;
    chart.setOption({
      series: [{ zoom: currentZoom * 1.2 }]
    });
  }
}

function zoomOut() {
  const chart = chartRef.value?.chart;
  if (chart) {
    const currentZoom = chart.getOption()?.series?.[0]?.zoom || 1;
    chart.setOption({
      series: [{ zoom: currentZoom * 0.8 }]
    });
  }
}

function resetView() {
  const chart = chartRef.value?.chart;
  if (chart) {
    chart.dispatchAction({
      type: 'restore'
    });
  }
}

// Watch for data changes and update chart
watch(() => [props.nodes, props.edges], () => {
  if (chartRef.value?.chart) {
    chartRef.value.chart.setOption({
      series: [{
        data: transformNodes.value,
        links: transformEdges.value
      }]
    });
  }
}, { deep: true });

// Initialize chart on mount
onMounted(() => {
  if (chartRef.value?.chart && hasData.value) {
    chartRef.value.chart.resize();
  }
});
</script>

<style scoped>
.graph-visualization {
  width: 100%;
  height: 100%;
  min-height: 400px;
  position: relative;
}

/* Loading State */
.graph-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
  gap: var(--space-4);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--color-border-light);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
}

/* Empty State */
.graph-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
  padding: var(--space-8);
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-4);
}

.empty-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.empty-description {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  max-width: 320px;
}

/* Graph Container */
.graph-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

/* Controls */
.graph-controls {
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  z-index: 10;
}

.control-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.control-btn:hover {
  background: var(--color-border-light);
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.control-btn:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.control-btn:active {
  transform: translateY(0);
}

.control-btn svg {
  width: 20px;
  height: 20px;
  color: var(--color-text-primary);
}

/* Legend */
.graph-legend {
  position: absolute;
  bottom: var(--space-4);
  left: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  z-index: 10;
  max-width: 200px;
  box-shadow: var(--shadow-sm);
}

.legend-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.legend-color {
  width: 16px;
  height: 3px;
  border-radius: var(--radius-full);
}

.legend-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

/* ECharts Graph */
.echarts-graph {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

/* Tooltip Styles (injected into ECharts) */
:deep(.tooltip-content) {
  padding: var(--space-2);
  max-width: 280px;
}

:deep(.tooltip-title) {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

:deep(.tooltip-type) {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

:deep(.tooltip-status) {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  margin-bottom: var(--space-2);
}

:deep(.tooltip-aliases) {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-2);
}

:deep(.tooltip-bio) {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
}

:deep(.tooltip-strength) {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-1);
}

:deep(.tooltip-description) {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
}

/* Responsive */
@media (max-width: 768px) {
  .graph-legend {
    bottom: var(--space-2);
    left: var(--space-2);
    padding: var(--space-3);
    max-width: 150px;
  }

  .legend-items {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-2);
  }

  .graph-controls {
    top: var(--space-2);
    right: var(--space-2);
  }

  .control-btn {
    width: 36px;
    height: 36px;
  }

  .control-btn svg {
    width: 16px;
    height: 16px;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .graph-container {
    border: 2px solid var(--color-border);
  }

  .control-btn {
    border-width: 2px;
  }

  .graph-legend {
    border-width: 2px;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .loading-spinner {
    animation: none;
  }

  .control-btn {
    transition: none;
  }
}
</style>
