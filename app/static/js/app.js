/**
 * app/static/js/app.js - 全局工具函数 + 主题管理
 */

// ═══════════════════════════════════════════════════════
// 主题管理
// ═══════════════════════════════════════════════════════
const ThemeManager = {
    STORAGE_KEY: 'fund-monitor-theme',
    THEMES: ['light', 'dark', 'system'],

    /** 初始化主题（尽早调用，避免闪烁） */
    init() {
        const saved = localStorage.getItem(this.STORAGE_KEY) || 'system';
        this.apply(saved);

        // 监听系统主题变化（当选择"跟随系统"时）
        window.matchMedia('(prefers-color-scheme: dark)')
            .addEventListener('change', () => {
                if (this.current() === 'system') {
                    this._updateCharts();
                }
            });
    },

    /** 获取当前保存的主题偏好 */
    current() {
        return localStorage.getItem(this.STORAGE_KEY) || 'system';
    },

    /** 获取实际生效的主题（system 会解析为 light 或 dark） */
    resolved() {
        const theme = this.current();
        if (theme !== 'system') return theme;
        return window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark' : 'light';
    },

    /** 应用主题 */
    apply(theme) {
        if (!this.THEMES.includes(theme)) theme = 'system';
        localStorage.setItem(this.STORAGE_KEY, theme);
        document.documentElement.setAttribute('data-theme', theme);
        this._updateButtons(theme);
    },

    /** 切换到下一个主题 */
    cycle() {
        const idx = this.THEMES.indexOf(this.current());
        const next = this.THEMES[(idx + 1) % this.THEMES.length];
        this.apply(next);
        this._updateCharts();
        const labels = { light: '浅色模式', dark: '深色模式', system: '跟随系统' };
        showToast(`已切换为${labels[next]}`, 'info');
    },

    /** 更新侧边栏按钮高亮 */
    _updateButtons(active) {
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === active);
        });
    },

    /** 通知 ECharts 刷新（切换主题后图表颜色可能需要更新） */
    _updateCharts() {
        // 给 ECharts 实例一点时间响应 CSS 变量变化
        setTimeout(() => {
            if (typeof echarts !== 'undefined') {
                document.querySelectorAll('[_echarts_instance_]').forEach(el => {
                    const instance = echarts.getInstanceByDom(el);
                    if (instance) instance.resize();
                });
            }
        }, 100);
    }
};

// 立即应用主题（在 DOM 解析前，防止闪烁）
ThemeManager.init();


// ═══════════════════════════════════════════════════════
// Toast 通知
// ═══════════════════════════════════════════════════════
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = {
        success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️'
    };
    const colors = {
        success: 'var(--success)', error: 'var(--danger)',
        warning: 'var(--warning)', info: 'var(--accent)'
    };

    const toast = document.createElement('div');
    toast.className = 'custom-toast p-3 mb-2 d-flex align-items-start gap-2';
    toast.style.borderLeft = `4px solid ${colors[type]}`;
    toast.innerHTML = `
        <span>${icons[type] || icons.info}</span>
        <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity .3s';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}


// ═══════════════════════════════════════════════════════
// API 请求封装
// ═══════════════════════════════════════════════════════
async function api(url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
    };
    const config = { ...defaults, ...options };
    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }

    try {
        const resp = await fetch(url, config);
        const data = await resp.json();
        if (!resp.ok) {
            throw new Error(data.detail || `请求失败 (${resp.status})`);
        }
        return data;
    } catch (err) {
        showToast(err.message, 'error');
        throw err;
    }
}


// ═══════════════════════════════════════════════════════
// 盈亏格式化
// ═══════════════════════════════════════════════════════
function formatMoney(value, showSign = true) {
    const sign = value >= 0 ? '+' : '';
    const prefix = showSign ? sign : '';
    return `${prefix}¥${Math.abs(value).toLocaleString('zh-CN', {
        minimumFractionDigits: 2, maximumFractionDigits: 2
    })}`;
}

function formatPct(value, showSign = true) {
    const sign = value >= 0 ? '+' : '';
    const prefix = showSign ? sign : '';
    return `${prefix}${value.toFixed(2)}%`;
}

function profitClass(value) {
    return value >= 0 ? 'text-profit' : 'text-loss';
}

function profitBadgeClass(value) {
    return value >= 0 ? 'badge-profit' : 'badge-loss';
}


// ═══════════════════════════════════════════════════════
// 确认对话框
// ═══════════════════════════════════════════════════════
function confirmDelete(message = '确认删除？此操作不可撤销。') {
    return confirm(message);
}


// ═══════════════════════════════════════════════════════
// 侧边栏高亮
// ═══════════════════════════════════════════════════════
function setActiveNav(path) {
    document.querySelectorAll('.sidebar-nav a').forEach(a => {
        a.classList.toggle('active', a.getAttribute('href') === path);
    });
}
