/**
 * PolyTheater Frontend API Module
 * 封装所有后端 API 调用
 */
import axios from 'axios'

// Axios 实例配置
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5001/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 可用于添加认证 token
api.interceptors.request.use(
  config => {
    // 如果有 token，添加到请求头
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  response => {
    // 后端返回格式: { success, data, message, timestamp }
    return response.data
  },
  error => {
    // 统一错误处理
    const errorMessage = error.response?.data?.error?.message || error.message
    console.error('API Error:', errorMessage)
    return Promise.reject(error)
  }
)

// ============================================
// 故事项目 API
// ============================================
export const storyApi = {
  // 创建项目
  create: (data) => api.post('/stories', data),
  
  // 获取单个项目
  get: (projectId) => api.get(`/stories/${projectId}`),
  
  // 列出项目
  list: (params = {}) => api.get('/stories', { params }),
  
  // 更新项目
  update: (projectId, data) => api.put(`/stories/${projectId}`, data),
  
  // 删除项目
  delete: (projectId) => api.delete(`/stories/${projectId}`)
}

// ============================================
// 知识图谱 API
// ============================================
export const graphApi = {
  // 构建图谱
  build: (projectId, data) => api.post(`/stories/${projectId}/graph/build`, data),
  
  // 获取构建状态
  getBuildStatus: (projectId) => api.get(`/stories/${projectId}/graph/build/status`),
  
  // 查询实体
  getEntities: (projectId, params = {}) => 
    api.get(`/stories/${projectId}/graph/entities`, { params }),
  
  // 查询关系
  getRelations: (projectId, params = {}) => 
    api.get(`/stories/${projectId}/graph/relations`, { params }),
  
  // 查询时间线
  getTimeline: (projectId, params = {}) => 
    api.get(`/stories/${projectId}/graph/timeline`, { params }),
  
  // 搜索图谱
  search: (projectId, data) => api.post(`/stories/${projectId}/graph/search`, data)
}

// ============================================
// 角色 API
// ============================================
export const characterApi = {
  // 创建角色
  create: (projectId, data) => api.post(`/stories/${projectId}/characters`, data),
  
  // 批量生成角色
  batchGenerate: (projectId, data) => 
    api.post(`/stories/${projectId}/characters/batch-generate`, data),
  
  // 获取角色列表
  list: (projectId, params = {}) => 
    api.get(`/stories/${projectId}/characters`, { params }),
  
  // 获取单个角色
  get: (projectId, characterId) => 
    api.get(`/stories/${projectId}/characters/${characterId}`),
  
  // 更新角色
  update: (projectId, characterId, data) => 
    api.put(`/stories/${projectId}/characters/${characterId}`, data),
  
  // 删除角色
  delete: (projectId, characterId) => 
    api.delete(`/stories/${projectId}/characters/${characterId}`),
  
  // 获取角色认知图谱
  getBeliefs: (projectId, characterId) => 
    api.get(`/stories/${projectId}/characters/${characterId}/beliefs`),
  
  // 更新角色认知
  updateBeliefs: (projectId, characterId, data) => 
    api.put(`/stories/${projectId}/characters/${characterId}/beliefs`, data)
}

// ============================================
// 模拟 API
// ============================================
export const simulationApi = {
  // 运行章节模拟
  runChapter: (projectId, chapter, data) => 
    api.post(`/stories/${projectId}/simulate/chapter/${chapter}`, data),
  
  // 获取模拟状态
  getStatus: (projectId, simulationId) => 
    api.get(`/stories/${projectId}/simulate/${simulationId}/status`),
  
  // 获取模拟结果
  getResult: (projectId, simulationId) => 
    api.get(`/stories/${projectId}/simulate/${simulationId}/result`),
  
  // 取消模拟
  cancel: (projectId, simulationId) => 
    api.delete(`/stories/${projectId}/simulate/${simulationId}`)
}

// ============================================
// 叙事生成 API
// ============================================
export const narrativeApi = {
  // 生成章节叙事
  generateChapter: (projectId, chapter, data) => 
    api.post(`/stories/${projectId}/narratives/chapter/${chapter}`, data),
  
  // 获取生成状态
  getStatus: (projectId, generationId) => 
    api.get(`/stories/${projectId}/narratives/${generationId}/status`),
  
  // 获取生成的叙事
  getResult: (projectId, generationId) => 
    api.get(`/stories/${projectId}/narratives/${generationId}/result`),
  
  // 获取已保存的章节叙事
  getChapter: (projectId, chapter) => 
    api.get(`/stories/${projectId}/chapters/${chapter}`),
  
  // 获取所有章节
  listChapters: (projectId) => 
    api.get(`/stories/${projectId}/chapters`)
}

// ============================================
// 一致性检查 API
// ============================================
export const checkApi = {
  // 检查时间线
  timeline: (projectId, data) => 
    api.post(`/stories/${projectId}/checks/timeline`, data),
  
  // 检查人物一致性
  character: (projectId, data) => 
    api.post(`/stories/${projectId}/checks/character`, data),
  
  // 检查认知冲突
  belief: (projectId, data) => 
    api.post(`/stories/${projectId}/checks/belief`, data),
  
  // 全面检查
  full: (projectId) => 
    api.post(`/stories/${projectId}/checks/full`)
}

// ============================================
// 控制配置 API
// ============================================
export const configApi = {
  // 获取配置
  get: (projectId) => api.get(`/stories/${projectId}/config`),
  
  // 更新配置
  update: (projectId, data) => api.put(`/stories/${projectId}/config`, data),
  
  // 添加里程碑
  addMilestone: (projectId, data) => 
    api.post(`/stories/${projectId}/config/milestones`, data),
  
  // 添加角色约束
  addConstraint: (projectId, characterId, data) => 
    api.post(`/stories/${projectId}/config/constraints/${characterId}`, data)
}

// ============================================
// 导出 API
// ============================================
export const exportApi = {
  // 导出项目
  project: (projectId, format = 'json') => 
    api.get(`/stories/${projectId}/export`, { params: { format } }),
  
  // 导出章节
  chapter: (projectId, chapter, format = 'md') => 
    api.get(`/stories/${projectId}/chapters/${chapter}/export`, { params: { format } }),
  
  // 导出全本
  full: (projectId, params = {}) => 
    api.get(`/stories/${projectId}/export/full`, { params })
}

// 默认导出 axios 实例
export default api
