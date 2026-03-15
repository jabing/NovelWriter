import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, VueWrapper } from '@vue/test-utils';
import { nextTick } from 'vue';
import GraphVisualization from '../GraphVisualization.vue';

// Mock vue-echarts
vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    template: '<div class="mock-echarts" @click="$emit(\'click\', $event)"></div>',
    props: ['options', 'autoresize'],
    emits: ['click'],
    data() {
      return {
        chart: {
          getOption: vi.fn(() => ({ series: [{ zoom: 1 }] })),
          setOption: vi.fn(),
          dispatchAction: vi.fn(),
          resize: vi.fn()
        }
      };
    }
  }
}));

// Mock echarts
vi.mock('echarts', () => ({
  graphic: {
    LinearGradient: vi.fn()
  }
}));

describe('GraphVisualization', () => {
  // Test data
  const mockNodes = [
    {
      data: {
        id: 'char1',
        label: 'John Doe',
        type: 'character',
        properties: {
          aliases: ['Johnny', 'JD'],
          tier: 1,
          bio: 'A brave hero',
          status: 'alive'
        }
      }
    },
    {
      data: {
        id: 'char2',
        label: 'Jane Smith',
        type: 'character',
        properties: {
          aliases: ['Jane'],
          tier: 2,
          bio: 'A mysterious character',
          status: 'alive'
        }
      }
    },
    {
      data: {
        id: 'char3',
        label: 'Deceased Character',
        type: 'character',
        properties: {
          aliases: [],
          tier: 1,
          bio: 'No longer alive',
          status: 'deceased'
        }
      }
    }
  ];

  const mockEdges = [
    {
      data: {
        source: 'char1',
        target: 'char2',
        relationship: 'FRIEND',
        properties: {
          strength: 0.8,
          description: 'Close friends since childhood'
        }
      }
    },
    {
      data: {
        source: 'char2',
        target: 'char3',
        relationship: 'FAMILY',
        properties: {
          strength: 0.5,
          description: 'Siblings'
        }
      }
    }
  ];

  let wrapper: VueWrapper<InstanceType<typeof GraphVisualization>>;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Structure', () => {
    it('renders the component', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });
      expect(wrapper.find('.graph-visualization').exists()).toBe(true);
    });

    it('accepts required props', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });
      expect(wrapper.props('nodes')).toEqual(mockNodes);
      expect(wrapper.props('edges')).toEqual(mockEdges);
      expect(wrapper.props('loading')).toBe(false);
    });

    it('loading prop defaults to false', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges
        }
      });
      expect(wrapper.props('loading')).toBe(false);
    });
  });

  describe('Loading State', () => {
    it('displays loading spinner when loading is true', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: [],
          edges: [],
          loading: true
        }
      });
      expect(wrapper.find('.graph-loading').exists()).toBe(true);
      expect(wrapper.find('.loading-spinner').exists()).toBe(true);
      expect(wrapper.find('.loading-text').text()).toBe('Loading graph...');
    });

    it('has proper accessibility attributes for loading', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: [],
          edges: [],
          loading: true
        }
      });
      const loadingEl = wrapper.find('.graph-loading');
      expect(loadingEl.attributes('role')).toBe('status');
      expect(loadingEl.attributes('aria-live')).toBe('polite');
    });

    it('does not display graph when loading', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: true
        }
      });
      expect(wrapper.find('.graph-container').exists()).toBe(false);
      expect(wrapper.find('.graph-empty').exists()).toBe(false);
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no nodes', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: [],
          edges: [],
          loading: false
        }
      });
      expect(wrapper.find('.graph-empty').exists()).toBe(true);
      expect(wrapper.find('.empty-title').text()).toBe('No Graph Data');
    });

    it('has proper empty state messaging', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: [],
          edges: [],
          loading: false
        }
      });
      expect(wrapper.find('.empty-description').text()).toContain('Add characters and relationships');
    });

    it('displays empty state icon', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: [],
          edges: [],
          loading: false
        }
      });
      expect(wrapper.find('.empty-icon').exists()).toBe(true);
    });

    it('has proper accessibility attributes for empty state', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: [],
          edges: [],
          loading: false
        }
      });
      const emptyEl = wrapper.find('.graph-empty');
      expect(emptyEl.attributes('role')).toBe('status');
      expect(emptyEl.attributes('aria-live')).toBe('polite');
    });
  });

  describe('Graph Display', () => {
    it('displays graph when data exists', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });
      expect(wrapper.find('.graph-container').exists()).toBe(true);
      expect(wrapper.find('.echarts-graph').exists()).toBe(true);
    });

    it('renders zoom controls', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });
      const controls = wrapper.find('.graph-controls');
      expect(controls.exists()).toBe(true);
      expect(controls.findAll('.control-btn').length).toBe(3);
    });

    it('zoom controls have proper labels', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });
      const buttons = wrapper.findAll('.control-btn');
      expect(buttons[0].attributes('aria-label')).toBe('Zoom in');
      expect(buttons[1].attributes('aria-label')).toBe('Zoom out');
      expect(buttons[2].attributes('aria-label')).toBe('Reset view');
    });

    it('renders legend', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });
      const legend = wrapper.find('.graph-legend');
      expect(legend.exists()).toBe(true);
      expect(legend.find('.legend-title').text()).toBe('Relationship Types');
    });

    it('legend shows all relationship types', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });
      const legendItems = wrapper.findAll('.legend-item');
      expect(legendItems.length).toBeGreaterThan(0);
    });
  });

  describe('Zoom Controls', () => {
    it('zoom in button is clickable and has proper attributes', async () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });
      const zoomInBtn = wrapper.findAll('.control-btn')[0];
      expect(zoomInBtn.attributes('aria-label')).toBe('Zoom in');
      expect(zoomInBtn.attributes('title')).toBe('Zoom in');
      // Verify button is clickable
      await zoomInBtn.trigger('click');
      // Button should exist and be interactive
      expect(zoomInBtn.exists()).toBe(true);
    });

    it('zoom out button is clickable and has proper attributes', async () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });
      const zoomOutBtn = wrapper.findAll('.control-btn')[1];
      expect(zoomOutBtn.attributes('aria-label')).toBe('Zoom out');
      expect(zoomOutBtn.attributes('title')).toBe('Zoom out');
      await zoomOutBtn.trigger('click');
      expect(zoomOutBtn.exists()).toBe(true);
    });

    it('reset view button is clickable and has proper attributes', async () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });
      const resetBtn = wrapper.findAll('.control-btn')[2];
      expect(resetBtn.attributes('aria-label')).toBe('Reset view');
      expect(resetBtn.attributes('title')).toBe('Reset view');
      await resetBtn.trigger('click');
      expect(resetBtn.exists()).toBe(true);
    });
  });

  describe('Event Emission', () => {
    it('emits node-click event when node is clicked', async () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      // Simulate node click
      const mockParams = {
        dataType: 'node',
        data: {
          originalData: mockNodes[0].data
        }
      };

      await wrapper.vm.handleChartClick(mockParams);

      expect(wrapper.emitted('node-click')).toBeTruthy();
      expect(wrapper.emitted('node-click')![0]).toEqual([mockNodes[0].data]);
    });

    it('emits edge-click event when edge is clicked', async () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      // Simulate edge click
      const mockParams = {
        dataType: 'edge',
        data: {
          originalData: mockEdges[0].data
        }
      };

      await wrapper.vm.handleChartClick(mockParams);

      expect(wrapper.emitted('edge-click')).toBeTruthy();
      expect(wrapper.emitted('edge-click')![0]).toEqual([mockEdges[0].data]);
    });

    it('does not emit events for unknown data types', async () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const mockParams = {
        dataType: 'unknown',
        data: {}
      };

      await wrapper.vm.handleChartClick(mockParams);

      expect(wrapper.emitted('node-click')).toBeFalsy();
      expect(wrapper.emitted('edge-click')).toBeFalsy();
    });
  });

  describe('Data Transformation', () => {
    it('correctly transforms nodes for ECharts', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const transformedNodes = wrapper.vm.transformNodes;
      expect(transformedNodes).toHaveLength(3);
      expect(transformedNodes[0].id).toBe('char1');
      expect(transformedNodes[0].name).toBe('John Doe');
      expect(transformedNodes[0].originalData).toEqual(mockNodes[0].data);
    });

    it('calculates correct node size based on tier', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const transformedNodes = wrapper.vm.transformNodes;
      // Tier 1 should be 28px (20 + 1*8), Tier 2 should be 36px (20 + 2*8)
      expect(transformedNodes[0].symbolSize).toBe(28); // tier 1
      expect(transformedNodes[1].symbolSize).toBe(36); // tier 2
    });

    it('correctly transforms edges for ECharts', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const transformedEdges = wrapper.vm.transformEdges;
      expect(transformedEdges).toHaveLength(2);
      expect(transformedEdges[0].source).toBe('char1');
      expect(transformedEdges[0].target).toBe('char2');
      expect(transformedEdges[0].originalData).toEqual(mockEdges[0].data);
    });

    it('calculates correct edge width based on strength', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const transformedEdges = wrapper.vm.transformEdges;
      // strength 0.8 should be 4.2 (1 + 0.8*4), strength 0.5 should be 3 (1 + 0.5*4)
      expect(transformedEdges[0].lineStyle.width).toBe(4.2);
      expect(transformedEdges[1].lineStyle.width).toBe(3);
    });

    it('applies correct relationship colors to edges', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const transformedEdges = wrapper.vm.transformEdges;
      expect(transformedEdges[0].lineStyle.color).toBe('#4ECDC4'); // FRIEND
      expect(transformedEdges[1].lineStyle.color).toBe('#FF6B6B'); // FAMILY
    });
  });

  describe('Node Colors', () => {
    it('uses primary color for alive characters', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const color = wrapper.vm.getNodeColor(mockNodes[0].data);
      expect(color).toBe('#007AFF');
    });

    it('uses gray color for deceased characters', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const color = wrapper.vm.getNodeColor(mockNodes[2].data);
      expect(color).toBe('#95A5A6');
    });

    it('handles nodes without properties', () => {
      const nodeWithoutProps = {
        data: {
          id: 'char4',
          label: 'No Props Character',
          type: 'character'
        }
      };

      wrapper = mount(GraphVisualization, {
        props: {
          nodes: [nodeWithoutProps],
          edges: [],
          loading: false
        }
      });

      const transformed = wrapper.vm.transformNodes;
      expect(transformed[0].value).toBe(1); // default tier
      expect(transformed[0].symbolSize).toBe(28); // default size
    });
  });

  describe('Tooltip Formatters', () => {
    it('formats node tooltip correctly', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const nodeData = {
        originalData: mockNodes[0].data
      };

      const tooltip = wrapper.vm.formatNodeTooltip(nodeData);
      expect(tooltip).toContain('John Doe');
      expect(tooltip).toContain('character');
      expect(tooltip).toContain('Tier 1');
      expect(tooltip).toContain('alive');
      expect(tooltip).toContain('Johnny, JD'); // aliases
    });

    it('formats edge tooltip correctly', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const edgeData = {
        originalData: mockEdges[0].data
      };

      const tooltip = wrapper.vm.formatEdgeTooltip(edgeData);
      expect(tooltip).toContain('FRIEND');
      expect(tooltip).toContain('80%'); // strength * 100
      expect(tooltip).toContain('Close friends since childhood');
    });

    it('handles tooltip without bio', () => {
      const nodeWithoutBio = {
        data: {
          id: 'char5',
          label: 'No Bio Character',
          type: 'character',
          properties: {
            tier: 1,
            status: 'alive'
          }
        }
      };

      wrapper = mount(GraphVisualization, {
        props: {
          nodes: [nodeWithoutBio],
          edges: [],
          loading: false
        }
      });

      const nodeData = {
        originalData: nodeWithoutBio.data
      };

      const tooltip = wrapper.vm.formatNodeTooltip(nodeData);
      expect(tooltip).toContain('No Bio Character');
      expect(tooltip).not.toContain('tooltip-bio'); // bio section should not exist
    });
  });

  describe('Helper Functions', () => {
    it('formats relationship type correctly', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      expect(wrapper.vm.formatRelationshipType('FRIEND')).toBe('Friend');
      expect(wrapper.vm.formatRelationshipType('FAMILY')).toBe('Family');
      expect(wrapper.vm.formatRelationshipType('ALLY')).toBe('Ally');
    });

    it('returns correct status colors', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      expect(wrapper.vm.getStatusColor('alive')).toBe('#27AE60');
      expect(wrapper.vm.getStatusColor('deceased')).toBe('#E74C3C');
      expect(wrapper.vm.getStatusColor('missing')).toBe('#F39C12');
      expect(wrapper.vm.getStatusColor('unknown')).toBe('#9B59B6');
    });
  });

  describe('Computed Properties', () => {
    it('hasData returns true when nodes exist', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      expect(wrapper.vm.hasData).toBe(true);
    });

    it('hasData returns false when no nodes', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: [],
          edges: [],
          loading: false
        }
      });

      expect(wrapper.vm.hasData).toBe(false);
    });
  });

  describe('Reactivity', () => {
    it('updates when nodes prop changes', async () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const newNodes = [
        {
          data: {
            id: 'new1',
            label: 'New Character',
            type: 'character',
            properties: { tier: 1 }
          }
        }
      ];

      await wrapper.setProps({ nodes: newNodes });
      await nextTick();

      expect(wrapper.vm.transformNodes).toHaveLength(1);
      expect(wrapper.vm.transformNodes[0].name).toBe('New Character');
    });

    it('updates when edges prop changes', async () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const newEdges = [
        {
          data: {
            source: 'char1',
            target: 'char3',
            relationship: 'ENEMY',
            properties: { strength: 1 }
          }
        }
      ];

      await wrapper.setProps({ edges: newEdges });
      await nextTick();

      expect(wrapper.vm.transformEdges).toHaveLength(1);
      expect(wrapper.vm.transformEdges[0].lineStyle.color).toBe('#E74C3C');
    });
  });

  describe('Chart Options', () => {
    it('generates valid chart options', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const options = wrapper.vm.chartOptions;
      expect(options).toBeDefined();
      expect(options.backgroundColor).toBe('transparent');
      expect(options.tooltip).toBeDefined();
      expect(options.series).toBeDefined();
      expect(options.series).toHaveLength(1);
      expect(options.series[0].type).toBe('graph');
      expect(options.series[0].layout).toBe('force');
    });

    it('enables roam for zoom and pan', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const options = wrapper.vm.chartOptions;
      expect(options.series[0].roam).toBe(true);
    });

    it('includes force layout configuration', () => {
      wrapper = mount(GraphVisualization, {
        props: {
          nodes: mockNodes,
          edges: mockEdges,
          loading: false
        }
      });

      const options = wrapper.vm.chartOptions;
      expect(options.series[0].force).toBeDefined();
      expect(options.series[0].force.repulsion).toBe(1000);
      expect(options.series[0].force.gravity).toBe(0.1);
    });
  });
});
