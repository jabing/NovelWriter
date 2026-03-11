export default {
  nav: {
    dashboard: '仪表盘',
    projects: '项目',
    reading: '阅读',
    agents: '智能体',
    writing: '写作',
    publish: '发布',
    settings: '设置'
  },
  dashboard: {
    title: 'NovelWriter 仪表盘',
    welcome: '欢迎使用 NovelWriter',
    welcomeSubtitle: '欢迎回来。这是您写作项目的概览。',
    recentActivity: '最近活动',
    quickActions: '快捷操作',
    newProject: '新建项目',
    openProject: '打开项目',
    viewAll: '查看全部',
    noRecentActivity: '暂无最近活动',
    noProjects: '暂无项目',
    noProjectsDesc: '通过创建第一个项目开始您的写作之旅。定义您故事的前提、角色和世界。',
    createFirstProject: '创建您的第一个项目',
    total: '{count} 个总计',
    complete: '完成',
    systemHealth: '系统状态',
    overallStatus: '总体状态',
    activeAgents: '活跃智能体',
    lastBackup: '上次备份',
    storageUsed: '已用存储',
    activityDescription: '{completed}/{total} 章节 • {words} 字'
  },
  project: {
    title: '项目',
    projects: '项目列表',
    create: '创建项目',
    edit: '编辑项目',
    delete: '删除项目',
    name: '项目名称',
    description: '项目描述',
    createdAt: '创建时间',
    updatedAt: '更新时间',
    wordCount: '字数统计',
    chapterCount: '章节数量',
    genre: '类型',
    confirmDelete: '确定要删除此项目吗？此操作不可撤销。',
    searchPlaceholder: '搜索项目...',
    viewCard: '卡片',
    viewTable: '表格',
    allGenres: '所有类型',
    allStatuses: '所有状态',
    noResults: '未找到项目',
    noResultsDesc: '请尝试调整搜索条件或筛选器',
    chapters: '章节',
    words: '字',
    complete: '完成',
    draft: '草稿',
    in_progress: '进行中',
    completed: '已完成',
    archived: '已归档'
  },
  projectDetail: {
    tabs: {
      overview: '概览',
      chapters: '章节',
      characters: '角色',
      settings: '设置'
    },
    actions: {
      edit: '编辑项目',
      addChapter: '添加章节',
      export: '导出'
    },
    notFound: {
      title: '项目未找到',
      description: '您查找的项目不存在或已被删除。',
      backButton: '返回项目列表'
    },
    aria: {
      goBack: '返回'
    },
    progress: {
      unit: '%'
    },
    overview: {
      premise: '前提',
      statistics: '统计',
      chapters: '章节',
      words: '字数',
      target: '目标',
      themes: '主题',
      details: '详情',
      pov: '视角',
      tone: '基调',
      audience: '受众',
      structure: '结构'
    },
    settings: {
      title: '项目设置'
    },
    empty: {
      chapters: '章节管理即将推出',
      chaptersHint: '已完成 {completed}/{total} 章节',
      characters: '角色管理即将推出',
      settings: '项目设置即将推出'
    }
  },
  chapter: {
    title: '章节',
    create: '新建章节',
    edit: '编辑章节',
    delete: '删除章节',
    name: '章节名称',
    content: '章节内容',
    wordCount: '字数',
    status: '状态',
    draft: '草稿',
    inProgress: '写作中',
    completed: '已完成',
    published: '已发布'
  },
  agent: {
    title: '智能体',
    status: '状态',
    role: '角色',
    capabilities: '能力',
    lastActive: '最后活动',
    actions: '操作',
    start: '启动',
    stop: '停止',
    restart: '重启',
    viewLogs: '查看日志'
  },
  agents: {
    page: {
      title: '智能体',
      subtitle: '管理您的 AI 写作助手'
    },
    stats: {
      activeAgents: '活跃智能体',
      totalAgents: '智能体总数'
    },
    list: {
      id: 'ID: {id}',
      lastSeen: '最后在线: {time}'
    }
  },
  publish: {
    title: '发布',
    subtitle: '将您的作品发布到各个平台',
    platform: '发布平台',
    format: '导出格式',
    status: '发布状态',
    publishNow: '立即发布',
    schedule: '定时发布',
    exportOnly: '仅导出',
    chapters: '章节',
    reads: '阅读数',
    manage: '管理',
    connect: '连接'
  },
  settings: {
    title: '设置',
    subtitle: '配置您的偏好和应用设置',
    qualityMode: {
      title: '质量模式'
    },
    qualityModes: {
      high: {
        label: '高质量',
        description: '最佳质量输出，包含详细分析'
      },
      medium: {
        label: '中等质量',
        description: '平衡质量和性能'
      },
      low: {
        label: '低质量',
        description: '最快生成速度，基础分析'
      }
    },
    language: {
      title: '语言',
      interfaceLabel: '界面语言',
      interfaceDescription: '选择您的首选语言'
    },
    apiConfig: {
      title: 'API 配置',
      apiKeyLabel: 'API 密钥',
      apiKeyDescription: '输入您的 API 密钥以使用 AI 服务',
      placeholder: '输入 API 密钥',
      show: '显示'
    },
    theme: {
      title: '主题',
      description: '选择您的首选主题',
      light: '浅色',
      dark: '深色'
    },
    general: '通用设置',
    appearance: '外观',
    auto: '跟随系统',
    editor: '编辑器设置',
    fontSize: '字体大小',
    fontFamily: '字体',
    lineHeight: '行高',
    ai: 'AI 设置',
    model: '模型',
    temperature: '温度',
    maxTokens: '最大令牌数',
    about: '关于'
  },
  common: {
    save: '保存',
    cancel: '取消',
    delete: '删除',
    edit: '编辑',
    create: '创建',
    clear: '清除',
    confirm: '确认',
    close: '关闭',
    loading: '加载中...',
    noData: '暂无数据',
    error: '错误',
    success: '成功',
    warning: '警告',
    info: '信息',
    search: '搜索',
    filter: '筛选',
    sort: '排序',
    refresh: '刷新',
    more: '更多',
    less: '收起',
    yes: '是',
    no: '否',
    justNow: '刚刚',
    daysAgo: '{n}天前',
    hoursAgo: '{n}小时前',
    minutesAgo: '{n}分钟前'
  },
  status: {
    online: '在线',
    offline: '离线',
    busy: '忙碌',
    error: '错误',
    idle: '空闲',
    connecting: '连接中',
    connected: '已连接',
    disconnected: '已断开',
    healthy: '健康',
    warning: '警告'
  },
  message: {
    saveSuccess: '保存成功',
    saveFailed: '保存失败',
    deleteSuccess: '删除成功',
    deleteFailed: '删除失败',
    createSuccess: '创建成功',
    createFailed: '创建失败',
    updateSuccess: '更新成功',
    updateFailed: '更新失败',
    confirmDelete: '确定要删除吗？',
    unsavedChanges: '有未保存的更改，确定要离开吗？',
    connectionLost: '连接已断开，正在重新连接...',
    connectionRestored: '连接已恢复'
  },
  validation: {
    required: '此项为必填',
    minLength: '最少需要 {min} 个字符',
    maxLength: '最多允许 {max} 个字符',
    invalidFormat: '格式不正确',
    invalidEmail: '请输入有效的邮箱地址'
  },
  wizard: {
    title: '创建新项目',
    step: '第 {current} 步，共 {total} 步',
    next: '下一步',
    previous: '上一步',
    finish: '创建项目',
    basicInfo: {
      title: '基本信息',
      description: '告诉我们你的故事'
    },
    premise: {
      title: '前提与主题',
      description: '定义你的故事基础'
    },
    structure: {
      title: '故事结构',
      description: '选择你的叙事框架'
    },
    targets: {
      title: '目标设定',
      description: '设定你的写作目标'
    },
    field: {
      title: '标题',
      titlePlaceholder: '输入你的故事标题',
      genre: '类型',
      genrePlaceholder: '选择一个类型',
      description: '描述',
      descriptionPlaceholder: '简要描述你的故事',
      premise: '故事前提',
      premisePlaceholder: '核心冲突或吸引点是什么？',
      themes: '主题',
      themesPlaceholder: '按回车添加主题',
      structure: '故事结构',
      targetWords: '目标字数',
      targetChapters: '目标章节',
      threeAct: '三幕式结构',
      threeActDesc: '铺垫、对抗、解决',
      fiveAct: '五幕式结构',
      fiveActDesc: '弗雷塔格金字塔，适合复杂叙事',
      herosJourney: '英雄之旅',
      herosJourneyDesc: '坎贝尔的英雄神话模式'
    },
    genre: {
      fantasy: '奇幻',
      scifi: '科幻',
      romance: '言情',
      mystery: '悬疑',
      thriller: '惊悚',
      horror: '恐怖',
      literary: '文学小说',
      historical: '历史小说',
      adventure: '冒险',
      youngAdult: '青春文学'
    },
    error: {
      titleRequired: '请输入项目标题',
      titleMinLength: '标题至少需要2个字符',
      genreRequired: '请选择一个类型'
    },
    success: '项目创建成功！'
  },
  character: {
    title: '角色',
    create: '新建角色',
    edit: '编辑角色',
    delete: '删除角色',
    view: '查看详情',
    name: '姓名',
    role: '角色类型',
    description: '描述',
    status: '状态',
    relationships: '关系',
    noCharacters: '暂无角色',
    noCharactersDesc: '添加角色开始构建你的故事',
    addFirst: '添加第一个角色',
    protagonist: '主角',
    antagonist: '反派',
    supporting: '配角',
    minor: '次要角色',
    active: '活跃',
    archived: '已归档'
  },
  bookshelf: {
    title: '书架',
    subtitle: '你的故事图书馆',
    continueReading: '继续阅读',
    completed: '已完成',
    chapters: '章',
    words: '字',
    continue: '继续',
    allBooks: '全部书籍',
    book: '本书',
    books: '本书',
    noBooks: '暂无书籍',
    noBooksDesc: '创建你的第一个项目开始阅读'
  }
};
,
  writing: {
    title: '写作工作台',
    subtitle: 'AI辅助创作，让写作更轻松',
    selectProject: '选择项目',
    noProjects: '暂无项目',
    createProject: '创建项目',
    chapters: '章节',
    noChapters: '暂无章节',
    addChapter: '添加章节',
    newChapter: '新章节',
    chapterTitle: '章节标题',
    configuration: '写作配置',
    genre: '类型',
    genreFantasy: '奇幻',
    genreScifi: '科幻',
    genreRomance: '言情',
    genreMystery: '悬疑',
    genreThriller: '惊悚',
    genreHorror: '恐怖',
    genreLiterary: '文学',
    genreHistorical: '历史',
    genreAdventure: '冒险',
    genreYoungAdult: '青春',
    writingStyle: '写作风格',
    styleLight: '轻松',
    styleBalanced: '平衡',
    styleSerious: '严肃',
    styleSuspenseful: '悬疑',
    stylePoetic: '诗意',
    wordCount: '目标字数',
    words: '字',
    plotPoints: '关键情节点',
    addPlotPoint: '添加情节点',
    generate: '生成内容',
    generating: '正在生成...',
    save: '保存章节',
    saving: '正在保存...',
    saved: '已保存',
    editor: '内容编辑',
    placeholder: '点击"生成内容"开始AI创作，或直接在此输入...',
    generateSuccess: '内容生成成功',
    generateError: '生成失败',
    saveSuccess: '章节已保存',
    saveError: '保存失败',
    confirmDelete: '确定删除此章节？',
    untitledChapter: '未命名章节'
  }
};
