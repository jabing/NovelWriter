<template>
  <div class="metrics-charts">
    <div class="chart-container">
      <h3 class="chart-title">Word Count Distribution</h3>
      <v-chart
        :options="wordCountChartOptions"
        autoresize
        class="echarts-chart"
      />
    </div>
    
    <div class="chart-container">
      <h3 class="chart-title">Execution Time Distribution</h3>
      <v-chart
        :options="executionTimeChartOptions"
        autoresize
        class="echarts-chart"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useAgentStore } from '@/stores/agentStore';
import * as echarts from 'echarts';
import VChart from 'vue-echarts';

const agentStore = useAgentStore();

// Chart options
const wordCountChartOptions = ref({
  title: {
    text: 'Word Count Distribution',
    left: 'center',
    textStyle: {
      color: 'var(--color-text-primary)',
      fontFamily: 'var(--font-family)',
      fontWeight: 'var(--font-weight-semibold)'
    }
  },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'var(--color-surface)',
    borderColor: 'var(--color-border)',
    borderWidth: 1,
    textStyle: {
      color: 'var(--color-text-primary)'
    },
    formatter: function(params: any) {
      return `${params[0].name}: ${params[0].value} documents`;
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true,
    backgroundColor: 'transparent'
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['0-100', '101-500', '501-1000', '1001-5000', '5001-10000', '10000+'],
    axisLine: {
      lineStyle: {
        color: 'var(--color-border)'
      }
    },
    axisLabel: {
      color: 'var(--color-text-secondary)',
      fontSize: 'var(--font-size-sm)'
    }
  },
  yAxis: {
    type: 'value',
    axisLine: {
      lineStyle: {
        color: 'var(--color-border)'
      }
    },
    axisLabel: {
      color: 'var(--color-text-secondary)',
      fontSize: 'var(--font-size-sm)'
    },
    splitLine: {
      lineStyle: {
        color: 'var(--color-border-light)'
      }
    }
  },
  series: [{
    name: 'Documents',
    type: 'bar',
    data: [0, 0, 0, 0, 0, 0],
    barWidth: '60%',
    itemStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'var(--color-primary)' },
        { offset: 1, color: 'var(--color-primary-dark)' }
      ]),
      borderRadius: [4, 4, 0, 0]
    },
    emphasis: {
      itemStyle: {
        color: 'var(--color-primary-dark)'
      }
    }
  }]
});

const executionTimeChartOptions = ref({
  title: {
    text: 'Execution Time Distribution',
    left: 'center',
    textStyle: {
      color: 'var(--color-text-primary)',
      fontFamily: 'var(--font-family)',
      fontWeight: 'var(--font-weight-semibold)'
    }
  },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'var(--color-surface)',
    borderColor: 'var(--color-border)',
    borderWidth: 1,
    textStyle: {
      color: 'var(--color-text-primary)'
    },
    formatter: function(params: any) {
      return `${params[0].name}: ${params[0].value} executions`;
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true,
    backgroundColor: 'transparent'
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['<1s', '1-5s', '5-10s', '10-30s', '30-60s', '>60s'],
    axisLine: {
      lineStyle: {
        color: 'var(--color-border)'
      }
    },
    axisLabel: {
      color: 'var(--color-text-secondary)',
      fontSize: 'var(--font-size-sm)'
    }
  },
  yAxis: {
    type: 'value',
    axisLine: {
      lineStyle: {
        color: 'var(--color-border)'
      }
    },
    axisLabel: {
      color: 'var(--color-text-secondary)',
      fontSize: 'var(--font-size-sm)'
    },
    splitLine: {
      lineStyle: {
        color: 'var(--color-border-light)'
      }
    }
  },
  series: [{
    name: 'Executions',
    type: 'bar',
    data: [0, 0, 0, 0, 0, 0],
    barWidth: '60%',
    itemStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'var(--color-secondary)' },
        { offset: 1, color: 'var(--color-accent)' }
      ]),
      borderRadius: [4, 4, 0, 0]
    },
    emphasis: {
      itemStyle: {
        color: 'var(--color-primary-dark)'
      }
    }
  }]
});

// Generate realistic histogram data
const generateWordCountData = () => {
  // Simulate realistic word count distribution
  return [
    Math.floor(Math.random() * 50) + 10,    // 0-100
    Math.floor(Math.random() * 80) + 30,    // 101-500  
    Math.floor(Math.random() * 60) + 20,    // 501-1000
    Math.floor(Math.random() * 40) + 10,    // 1001-5000
    Math.floor(Math.random() * 20) + 5,     // 5001-10000
    Math.floor(Math.random() * 10) + 2      // 10000+
  ];
};

const generateExecutionTimeData = () => {
  // Simulate realistic execution time distribution
  return [
    Math.floor(Math.random() * 15) + 5,    // <1s
    Math.floor(Math.random() * 12) + 8,    // 1-5s
    Math.floor(Math.random() * 8) + 4,     // 5-10s
    Math.floor(Math.random() * 6) + 2,     // 10-30s
    Math.floor(Math.random() * 3) + 1,     // 30-60s
    Math.floor(Math.random() * 2) + 1      // >60s
  ];
};

// Update charts with real-time data
const updateCharts = () => {
  const wordCountData = generateWordCountData();
  const executionTimeData = generateExecutionTimeData();
  
  // Update charts with data
  if (wordCountChartOptions.value?.series?.[0]) {
    wordCountChartOptions.value.series[0].data = wordCountData;
    wordCountChartOptions.value = { ...wordCountChartOptions.value };
  }
  if (executionTimeChartOptions.value?.series?.[0]) {
    executionTimeChartOptions.value.series[0].data = executionTimeData;
    executionTimeChartOptions.value = { ...executionTimeChartOptions.value };
  }
};

// Initialize and update charts
onMounted(() => {
  // Initial update
  updateCharts();
  
  // Set up interval for real-time updates (every 3 seconds)
  const interval = setInterval(updateCharts, 3000);
  
  // Clean up interval on unmount
  onUnmounted(() => {
    clearInterval(interval);
  });
});

// Watch for agent store changes to trigger updates
watch(() => agentStore.agents, () => {
  updateCharts();
}, { deep: true });
</script>

<style scoped>
.metrics-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-6);
  padding: var(--space-6);
}

.chart-container {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.chart-container:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.chart-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
  text-align: center;
}

.echarts-chart {
  width: 100%;
  height: 320px;
}

@media (max-width: 768px) {
  .metrics-charts {
    grid-template-columns: 1fr;
  }
}
</style>