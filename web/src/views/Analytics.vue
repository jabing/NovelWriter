<template>
  <div class="analytics-dashboard" role="main" aria-label="Analytics Dashboard" tabindex="0">
    <!-- Header -->
    <header class="dashboard-header" role="banner">
      <div class="header-actions">
        <div class="filter-controls" role="group" aria-label="Filter controls">
          <label class="filter-label" for="timeRange">Time Range:</label>
          <select class="filter-select" id="timeRange" v-model="selectedTimeRange" aria-label="Select time range" @change="handleFilterChange">
            <option value="7">Last 7 Days</option>
            <option value="30">Last 30 Days</option>
            <option value="90">Last 90 Days</option>
            <option value="365">Last Year</option>
          </select>
          
          <label class="filter-label" for="platform">Platform:</label>
          <select class="filter-select" id="platform" v-model="selectedPlatform" aria-label="Select platform" @change="handleFilterChange">
            <option value="all">All Platforms</option>
            <option value="web">Web</option>
            <option value="ios">iOS</option>
            <option value="android">Android</option>
            <option value="kindle">Kindle</option>
            <option value="other">Other</option>
          </select>
          
          <button class="apply-filter-btn" @click="applyFilters" aria-label="Apply filters" @keydown.space.prevent="applyFilters" @keydown.enter.prevent="applyFilters">
            Apply Filters
          </button>
        </div>
        
        <button class="export-btn" @click="exportDashboard" aria-label="Export dashboard data" @keydown.space.prevent="exportDashboard" @keydown.enter.prevent="exportDashboard">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="export-icon" aria-hidden="true">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="7,10 12,15 17,10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Export Dashboard
        </button>
      </div>
      <h1 class="dashboard-title" id="dashboard-title">Analytics Dashboard</h1>
      <p class="dashboard-subtitle" id="dashboard-description">Track your writing performance and engagement metrics</p>
    </header>

<!-- Statistics Cards -->
<section class="stats-grid" aria-labelledby="dashboard-title">
  <div class="stat-card" role="article" aria-labelledby="total-words-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
    <div class="stat-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M9 7h6m0 10v-3m-3 3v-8m-5 8h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
      </svg>
    </div>
    <div class="stat-content">
      <div class="stat-value" id="total-words-value">{{ totalWords.toLocaleString() }}</div>
      <div class="stat-label" id="total-words-label">Total Words</div>
      <div class="sr-only" aria-live="polite" aria-atomic="true">
        {{ totalWords.toLocaleString() }} total words
      </div>
    </div>
  </div>

  <div class="stat-card" role="article" aria-labelledby="reading-time-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
    <div class="stat-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
    </div>
    <div class="stat-content">
      <div class="stat-value" id="reading-time-value">{{ averageReadingTime }}</div>
      <div class="stat-label" id="reading-time-label">Reading Time</div>
      <div class="sr-only" aria-live="polite" aria-atomic="true">
        {{ averageReadingTime }} average reading time
      </div>
    </div>
  </div>

  <div class="stat-card" role="article" aria-labelledby="readers-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
    <div class="stat-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 00-3-3.87"/>
        <path d="M16 3.13a4 4 0 010 7.75"/>
      </svg>
    </div>
    <div class="stat-content">
      <div class="stat-value" id="readers-value">{{ totalReaders.toLocaleString() }}</div>
      <div class="stat-label" id="readers-label">Readers</div>
      <div class="sr-only" aria-live="polite" aria-atomic="true">
        {{ totalReaders.toLocaleString() }} total readers
      </div>
    </div>
  </div>

  <div class="stat-card" role="article" aria-labelledby="engagement-rate-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
    <div class="stat-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 00.5-7H9"/>
      </svg>
    </div>
    <div class="stat-content">
      <div class="stat-value" id="engagement-rate-value">{{ engagementRate }}%</div>
      <div class="stat-label" id="engagement-rate-label">Engagement Rate</div>
      <div class="sr-only" aria-live="polite" aria-atomic="true">
        {{ engagementRate }} percent engagement rate
      </div>
    </div>
  </div>

  <!-- Additional Analytics Cards -->
  <div class="stat-card" role="article" aria-labelledby="chapters-completed-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
    <div class="stat-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 6h16M4 10h16M4 14h16M4 18h16"/>
      </svg>
    </div>
    <div class="stat-content">
      <div class="stat-value">{{ chaptersCompleted }}</div>
      <div class="stat-label" id="chapters-completed-label">Chapters Completed</div>
      <div class="sr-only" aria-live="polite" aria-atomic="true">
        {{ chaptersCompleted }} chapters completed
      </div>
    </div>
  </div>

  <div class="stat-card" role="article" aria-labelledby="avg-words-chapter-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
    <div class="stat-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
      </svg>
    </div>
    <div class="stat-content">
      <div class="stat-value">{{ averageWordsPerChapter.toLocaleString() }}</div>
      <div class="stat-label" id="avg-words-chapter-label">Avg Words/Chapter</div>
      <div class="sr-only" aria-live="polite" aria-atomic="true">
        {{ averageWordsPerChapter.toLocaleString() }} average words per chapter
      </div>
    </div>
  </div>

  <div class="stat-card" role="article" aria-labelledby="reader-growth-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
    <div class="stat-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M23 6l-9.5 9.5-5-5L1 18"/>
      </svg>
    </div>
    <div class="stat-content">
      <div class="stat-value">{{ readerGrowthRate }}%</div>
      <div class="stat-label" id="reader-growth-label">Reader Growth</div>
      <div class="sr-only" aria-live="polite" aria-atomic="true">
        {{ readerGrowthRate }} percent reader growth
      </div>
    </div>
  </div>

  <div class="stat-card" role="article" aria-labelledby="completion-rate-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
    <div class="stat-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>
    </div>
    <div class="stat-content">
      <div class="stat-value">{{ completionRate }}%</div>
      <div class="stat-label" id="completion-rate-label">Completion Rate</div>
      <div class="sr-only" aria-live="polite" aria-atomic="true">
        {{ completionRate }} percent completion rate
      </div>
    </div>
  </div>
</section>

    <!-- Engagement Trends Chart -->
    <div class="chart-container" role="region" aria-labelledby="engagement-trends-title" aria-describedby="engagement-trends-description" tabindex="0">
      <h3 class="chart-title" id="engagement-trends-title">Engagement Trends</h3>
      <p class="chart-description" id="engagement-trends-description" aria-live="polite" aria-atomic="true">
        Line chart showing reader engagement over time
      </p>
      <v-chart
        :options="engagementTrendsOptions"
        autoresize
        class="echarts-chart"
        @chart:click="handleChartClick"
        @chart:hover="handleChartHover"
      />
      <div class="chart-accessibility-info" aria-live="polite" aria-atomic="true">
        <p>Engagement trends chart showing daily reader activity over the selected time period</p>
      </div>
    </div>

<!-- Platform Comparison Chart -->
<div class="chart-container" role="region" aria-labelledby="platform-comparison-title" aria-describedby="platform-comparison-description" tabindex="0">
  <h3 class="chart-title" id="platform-comparison-title">Platform Comparison</h3>
  <p class="chart-description" id="platform-comparison-description" aria-live="polite" aria-atomic="true">
    Bar chart comparing engagement across different platforms
  </p>
  <v-chart
    :options="platformComparisonOptions"
    autoresize
    class="echarts-chart"
    @chart:click="handleChartClick"
    @chart:hover="handleChartHover"
  />
  <div class="chart-accessibility-info" aria-live="polite" aria-atomic="true">
    <p>Platform comparison chart showing engagement percentages across different reading platforms</p>
  </div>
</div>

<!-- Engagement Metrics -->
<div class="metrics-section" role="region" aria-labelledby="engagement-metrics-title" tabindex="0">
  <h3 class="section-title" id="engagement-metrics-title">Engagement Metrics</h3>
  <div class="metrics-grid">
    <div class="metric-card" role="article" aria-labelledby="daily-readers-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
      <div class="metric-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </div>
      <div class="metric-content">
        <div class="metric-value">{{ dailyEngagement }}</div>
        <div class="metric-label" id="daily-readers-label">Daily Readers</div>
        <div class="sr-only" aria-live="polite" aria-atomic="true">
          {{ dailyEngagement }} daily readers
        </div>
      </div>
    </div>

    <div class="metric-card" role="article" aria-labelledby="weekly-readers-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
      <div class="metric-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </div>
      <div class="metric-content">
        <div class="metric-value">{{ weeklyEngagement.toLocaleString() }}</div>
        <div class="metric-label" id="weekly-readers-label">Weekly Readers</div>
        <div class="sr-only" aria-live="polite" aria-atomic="true">
          {{ weeklyEngagement.toLocaleString() }} weekly readers
        </div>
      </div>
    </div>

    <div class="metric-card" role="article" aria-labelledby="monthly-readers-label" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
      <div class="metric-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </div>
      <div class="metric-content">
        <div class="metric-value">{{ monthlyEngagement.toLocaleString() }}</div>
        <div class="metric-label" id="monthly-readers-label">Monthly Readers</div>
        <div class="sr-only" aria-live="polite" aria-atomic="true">
          {{ monthlyEngagement.toLocaleString() }} monthly readers
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Recent Activity -->
    <div class="activity-section" role="region" aria-labelledby="recent-activity-title" tabindex="0">
      <h3 class="section-title" id="recent-activity-title">Recent Activity</h3>
      <div class="activity-list">
        <div class="activity-item" role="article" aria-labelledby="activity-1-title" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
          <div class="activity-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="7,10 12,15 17,10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </div>
          <div class="activity-content">
            <div class="activity-title" id="activity-1-title">Chapter 5 Published</div>
            <div class="activity-time">2 hours ago</div>
            <div class="sr-only" aria-live="polite" aria-atomic="true">
              Chapter 5 published 2 hours ago
            </div>
          </div>
        </div>

        <div class="activity-item" role="article" aria-labelledby="activity-2-title" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
          <div class="activity-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="7,10 12,15 17,10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </div>
          <div class="activity-content">
            <div class="activity-title" id="activity-2-title">Chapter 4 Updated</div>
            <div class="activity-time">5 hours ago</div>
            <div class="sr-only" aria-live="polite" aria-atomic="true">
              Chapter 4 updated 5 hours ago
            </div>
          </div>
        </div>

        <div class="activity-item" role="article" aria-labelledby="activity-3-title" tabindex="0" @keydown.space.prevent @keydown.enter.prevent>
          <div class="activity-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="7,10 12,15 17,10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </div>
          <div class="activity-content">
            <div class="activity-title" id="activity-3-title">Chapter 3 Draft Completed</div>
            <div class="activity-time">1 day ago</div>
            <div class="sr-only" aria-live="polite" aria-atomic="true">
              Chapter 3 draft completed 1 day ago
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import VChart from 'vue-echarts';
import { useProjectStore } from '../stores/projectStore';

// Chart hover information element
const chartHoverInfo = ref<HTMLElement | null>(null);

const projectStore = useProjectStore();

// Filter state
const selectedTimeRange = ref('30');
const selectedPlatform = ref('all');

// Engagement Trends Chart Options
const engagementTrendsOptions = ref({
  title: {
    text: 'Engagement Trends',
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
      return `${params[0].name}: ${params[0].value} readers`;
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
    data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
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
    name: 'Readers',
    type: 'line',
    data: [120, 132, 101, 134, 90, 230, 210],
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    lineStyle: {
      color: 'var(--color-primary)',
      width: 3,
      shadowColor: 'rgba(0, 122, 255, 0.3)',
      shadowBlur: 10
    },
    itemStyle: {
      color: 'var(--color-primary)',
      borderColor: '#fff',
      borderWidth: 2
    },
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(0, 122, 255, 0.3)' },
        { offset: 1, color: 'rgba(0, 122, 255, 0.05)' }
      ])
    },
    emphasis: {
      focus: 'series'
    }
  }]
});

// Platform Comparison Chart Options
const platformComparisonOptions = ref({
  title: {
    text: 'Platform Comparison',
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
      return `${params[0].name}: ${params[0].value}%`;
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
    data: ['Web', 'iOS', 'Android', 'Kindle', 'Other'],
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
    name: 'Engagement',
    type: 'bar',
    data: [65, 78, 45, 89, 32],
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

// Calculate statistics from project data
const totalWords = computed(() => {
  return projectStore.projects.reduce((total, project) => {
    return total + ((project as any).wordCount || 0);
  }, 0);
});

const averageReadingTime = computed(() => {
  const totalWords = projectStore.projects.reduce((total, project) => {
    return total + ((project as any).wordCount || 0);
  }, 0);
  const wordCount = totalWords || 1;
  const readingTimeInMinutes = (wordCount / 200); // Assuming 200 words per minute
  const hours = Math.floor(readingTimeInMinutes / 60);
  const minutes = Math.round(readingTimeInMinutes % 60);
  return hours > 0 ? `${hours}.${minutes}h` : `${minutes}m`;
});

const totalReaders = computed(() => {
  return projectStore.projects.reduce((total, project) => {
    return total + ((project as any).readers || 0);
  }, 0);
});

const engagementRate = computed(() => {
  const totalReaders = projectStore.projects.reduce((total, project) => {
    return total + ((project as any).readers || 0);
  }, 0);
  const totalWords = projectStore.projects.reduce((total, project) => {
    return total + ((project as any).wordCount || 0);
  }, 0);
  if (totalWords === 0) return 0;
  return Math.round((totalReaders / totalWords) * 100);
});

// Additional analytics features
const chaptersCompleted = computed(() => {
  return projectStore.projects.reduce((total, project) => {
    return total + ((project as any).chapters?.length || 0);
  }, 0);
});

const averageWordsPerChapter = computed(() => {
  const totalWords = projectStore.projects.reduce((total, project) => {
    return total + ((project as any).wordCount || 0);
  }, 0);
  const totalChapters = projectStore.projects.reduce((total, project) => {
    return total + ((project as any).chapters?.length || 0);
  }, 0);
  if (totalChapters === 0) return 0;
  return Math.round(totalWords / totalChapters);
});

const readerGrowthRate = computed(() => {
  const totalReaders = projectStore.projects.reduce((total, project) => {
    return total + ((project as any).readers || 0);
  }, 0);
  // Simulate growth rate calculation (in real app, this would use historical data)
  return Math.round((totalReaders / 1000) * 100); // Example: 10% growth for 1000 readers
});

const completionRate = computed(() => {
  const totalReaders = projectStore.projects.reduce((total, project) => {
    return total + ((project as any).readers || 0);
  }, 0);
  const totalWords = projectStore.projects.reduce((total, project) => {
    return total + ((project as any).wordCount || 0);
  }, 0);
  if (totalWords === 0) return 0;
  return Math.round((totalReaders / (totalWords / 500)) * 100); // Assuming 500 words per reader
});

const dailyEngagement = computed(() => {
  return Math.floor(Math.random() * 50) + 100; // Simulated daily engagement
});

const weeklyEngagement = computed(() => {
  return Math.floor(Math.random() * 200) + 500; // Simulated weekly engagement
});

const monthlyEngagement = computed(() => {
  return Math.floor(Math.random() * 500) + 2000; // Simulated monthly engagement
});

// Accessibility functions
const handleFilterChange = () => {
  // Announce filter change to screen readers
  const filterAnnouncement = document.createElement('div');
  filterAnnouncement.setAttribute('aria-live', 'polite');
  filterAnnouncement.setAttribute('aria-atomic', 'true');
  filterAnnouncement.textContent = `Filters applied: Time range - ${selectedTimeRange.value} days, Platform - ${selectedPlatform.value}`;
  document.body.appendChild(filterAnnouncement);
  setTimeout(() => {
    document.body.removeChild(filterAnnouncement);
  }, 3000);
};

// Filter functions
const applyFilters = () => {
  // In a real application, this would filter the data based on selectedTimeRange and selectedPlatform
  console.log('Applying filters:', selectedTimeRange.value, selectedPlatform.value);
  // Update charts with filtered data
  updateCharts();
  handleFilterChange();
};

// Chart interaction handlers
const handleChartClick = (params: any) => {
  // Announce chart interaction to screen readers
  const chartAnnouncement = document.createElement('div');
  chartAnnouncement.setAttribute('aria-live', 'polite');
  chartAnnouncement.setAttribute('aria-atomic', 'true');
  chartAnnouncement.textContent = `Chart clicked: ${params.name} - ${params.value}`;
  document.body.appendChild(chartAnnouncement);
  setTimeout(() => {
    document.body.removeChild(chartAnnouncement);
  }, 3000);
};

const handleChartHover = (params: any) => {
  // Update hover information for screen readers
  if (params) {
    const hoverInfo = document.getElementById('chart-hover-info');
    if (hoverInfo) {
      hoverInfo.textContent = `Hovering over: ${params.name} - ${params.value}`;
    }
  }
};

// Generate engagement data with filters
const generateEngagementData = () => {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  // days count is calculated for potential future use
  void (parseInt(selectedTimeRange.value || '0') / 7);
  return days.map(() => {
    return Math.floor(Math.random() * 100) + 50;
  });
};

// Generate platform data with filters
const generatePlatformData = () => {
  const platforms = ['Web', 'iOS', 'Android', 'Kindle', 'Other'];
  if (selectedPlatform.value !== 'all') {
    const platformIndex = platforms.indexOf(selectedPlatform.value.charAt(0).toUpperCase() + selectedPlatform.value.slice(1));
    return [platformIndex >= 0 ? 100 : 0, 0, 0, 0, 0];
  }
  return [
    Math.floor(Math.random() * 20) + 60,     // Web
    Math.floor(Math.random() * 15) + 75,     // iOS
    Math.floor(Math.random() * 25) + 40,     // Android
    Math.floor(Math.random() * 20) + 80,     // Kindle
    Math.floor(Math.random() * 15) + 25      // Other
  ];
};

// Update charts with real-time data
const updateCharts = () => {
  const engagementData = generateEngagementData();
  const platformData = generatePlatformData();
  
  // Update series data directly - TypeScript allows this with variable assignment
  if (engagementTrendsOptions.value.series && engagementTrendsOptions.value.series.length > 0) {
    (engagementTrendsOptions.value.series[0] as any).data = engagementData;
  }
  if (platformComparisonOptions.value.series && platformComparisonOptions.value.series.length > 0) {
    (platformComparisonOptions.value.series[0] as any).data = platformData;
  }
  
  // Trigger reactivity by spreading
  engagementTrendsOptions.value = { ...engagementTrendsOptions.value };
  platformComparisonOptions.value = { ...platformComparisonOptions.value };
};

// Export dashboard functionality
const exportDashboard = () => {
  // Export engagement trends chart
  const engagementChart = document.querySelector('.echarts-chart:nth-child(1) canvas');
  if (engagementChart) {
    const engagementUrl = (engagementChart as HTMLCanvasElement).toDataURL('image/png');
    downloadImage(engagementUrl, 'engagement-trends.png');
  }
  
  // Export platform comparison chart
  const platformChart = document.querySelector('.echarts-chart:nth-child(2) canvas');
  if (platformChart) {
    const platformUrl = (platformChart as HTMLCanvasElement).toDataURL('image/png');
    downloadImage(platformUrl, 'platform-comparison.png');
  }
  
  // Export statistics as CSV
  exportStatisticsAsCSV();
};

const downloadImage = (url: string, filename: string) => {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const exportStatisticsAsCSV = () => {
  const stats = {
    'Total Words': totalWords.value,
    'Reading Time': averageReadingTime.value,
    'Total Readers': totalReaders.value,
    'Engagement Rate': `${engagementRate.value}%`,
    'Chapters Completed': chaptersCompleted.value,
    'Avg Words/Chapter': averageWordsPerChapter.value,
    'Reader Growth': `${readerGrowthRate.value}%`,
    'Completion Rate': `${completionRate.value}%`,
    'Daily Readers': dailyEngagement.value,
    'Weekly Readers': weeklyEngagement.value,
    'Monthly Readers': monthlyEngagement.value
  };
  
  const headers = Object.keys(stats);
  const values = Object.values(stats);
  
  let csv = headers.join(',') + '\n';
  csv += values.join(',') + '\n';
  
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'analytics-statistics.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

// Initialize and update charts
onMounted(() => {
  // Initial update
  updateCharts();
  
  // Set up interval for real-time updates (every 5 seconds)
  const interval = setInterval(updateCharts, 5000);
  
  // Clean up interval on unmount
  onUnmounted(() => {
    clearInterval(interval);
  });
});

// Add chart hover info element to body
onMounted(() => {
  const hoverInfo = document.createElement('div');
  hoverInfo.id = 'chart-hover-info';
  hoverInfo.setAttribute('aria-live', 'polite');
  hoverInfo.setAttribute('aria-atomic', 'true');
  hoverInfo.style.position = 'absolute';
  hoverInfo.style.top = '0';
  hoverInfo.style.left = '0';
  hoverInfo.style.width = '1px';
  hoverInfo.style.height = '1px';
  hoverInfo.style.overflow = 'hidden';
  hoverInfo.style.clip = 'rect(0 0 0 0)';
  hoverInfo.style.whiteSpace = 'nowrap';
  document.body.appendChild(hoverInfo);
  chartHoverInfo.value = hoverInfo;
});

// Clean up chart hover info element
onUnmounted(() => {
  if (chartHoverInfo.value) {
    document.body.removeChild(chartHoverInfo.value);
  }
});
</script>

<style scoped>
.analytics-dashboard {
  padding: var(--space-6);
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: var(--space-8);
  text-align: center;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-4);
}

.header-actions {
  display: flex;
  gap: var(--space-4);
  align-items: center;
}

.filter-controls {
  display: flex;
  gap: var(--space-2);
  align-items: center;
}

.filter-select {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  min-width: 120px;
}

.apply-filter-btn {
  background: var(--color-secondary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: background-color var(--transition-base);
}

.apply-filter-btn:hover {
  background: var(--color-secondary-dark);
}

.apply-filter-btn:focus {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.3);
}

.export-btn {
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  transition: background-color var(--transition-base);
}

.export-btn:hover {
  background: var(--color-primary-dark);
}

.export-btn:focus {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.3);
}

.export-icon {
  width: 16px;
  height: 16px;
}

.dashboard-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.dashboard-subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.stat-card {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.stat-card:focus {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.stat-card:active {
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.chart-container {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  margin-bottom: var(--space-8);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.chart-container:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.chart-container:focus {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
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

.chart-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-4);
  text-align: center;
}

.chart-accessibility-info {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: var(--color-surface-light);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.echarts-chart {
  width: 100%;
  height: 400px;
}

.activity-section {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  margin-bottom: var(--space-8);
}

.activity-section:focus {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
  box-shadow: var(--shadow-card-hover);
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.activity-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  transition: background-color var(--transition-base);
  cursor: pointer;
}

.activity-item:hover {
  background: var(--color-border-light);
}

.activity-item:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  background: var(--color-border-light);
}

.activity-item:active {
  transform: scale(0.98);
}

.activity-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  color: white;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.activity-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.metrics-section {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  margin-bottom: var(--space-8);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.metrics-section:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.metrics-section:focus {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
  margin-top: var(--space-4);
}

.metric-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  transition: background-color var(--transition-base);
  cursor: pointer;
}

.metric-card:hover {
  background: var(--color-border-light);
}

.metric-card:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  background: var(--color-border-light);
}

.metric-card:active {
  transform: scale(0.98);
}

.metric-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-secondary);
  border-radius: var(--radius-full);
  color: white;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.metric-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* Focus ring styles for better accessibility */
:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Ensure sufficient color contrast */
:root {
  --color-text-primary-contrast: var(--color-text-primary);
  --color-text-secondary-contrast: var(--color-text-secondary);
  --color-text-tertiary-contrast: var(--color-text-tertiary);
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .stat-card {
    border: 2px solid var(--color-border);
  }
  
  .chart-container {
    border: 2px solid var(--color-border);
  }
  
  .activity-section {
    border: 2px solid var(--color-border);
  }
  
  .metrics-section {
    border: 2px solid var(--color-border);
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .stat-card {
    transition: none;
  }
  
  .chart-container {
    transition: none;
  }
  
  .activity-section {
    transition: none;
  }
  
  .metrics-section {
    transition: none;
  }
  
  .activity-item {
    transition: none;
  }
  
  .metric-card {
    transition: none;
  }
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .echarts-chart {
    height: 300px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}

.dashboard-header {
  margin-bottom: var(--space-8);
  text-align: center;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-4);
}

.header-actions {
  display: flex;
  gap: var(--space-4);
  align-items: center;
}

.filter-controls {
  display: flex;
  gap: var(--space-2);
  align-items: center;
}

.filter-select {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  min-width: 120px;
}

.apply-filter-btn {
  background: var(--color-secondary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: background-color var(--transition-base);
}

.apply-filter-btn:hover {
  background: var(--color-secondary-dark);
}

.export-btn {
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  transition: background-color var(--transition-base);
}

.export-btn:hover {
  background: var(--color-primary-dark);
}

.export-icon {
  width: 16px;
  height: 16px;
}

.export-btn {
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  transition: background-color var(--transition-base);
}

.export-btn:hover {
  background: var(--color-primary-dark);
}

.export-icon {
  width: 16px;
  height: 16px;
}

.dashboard-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.dashboard-subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.stat-card {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.chart-container {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  margin-bottom: var(--space-8);
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
  height: 400px;
}

.activity-section {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  margin-bottom: var(--space-8);
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.activity-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  transition: background-color var(--transition-base);
}

.activity-item:hover {
  background: var(--color-border-light);
}

.activity-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  color: white;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.activity-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.metrics-section {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  margin-bottom: var(--space-8);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.metrics-section:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
  margin-top: var(--space-4);
}

.metric-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  transition: background-color var(--transition-base);
}

.metric-card:hover {
  background: var(--color-border-light);
}

.metric-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-secondary);
  border-radius: var(--radius-full);
  color: white;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.metric-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .echarts-chart {
    height: 300px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>