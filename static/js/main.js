// 通用工具函数

/**
 * 显示 Toast 通知
 * @param {string} message  提示文字
 * @param {'success'|'error'|'info'} type  类型（默认 success）
 */
function showToast(message, type = 'success') {
    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type] ?? icons.info}</span><span>${message}</span>`;
    container.appendChild(toast);

    // 动画结束后移除 DOM（总时长 = 2.5s 显示 + 0.25s 淡出）
    setTimeout(() => toast.remove(), 2800);
}


function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

// 显示加载提示
function showLoading(message = '加载中...') {
    // 可以实现一个全局的加载提示
    console.log(message);
}

// 隐藏加载提示
function hideLoading() {
    console.log('加载完成');
}

// 显示错误提示
function showError(message) {
    alert(message);
}

// 显示成功提示
function showSuccess(message) {
    alert(message);
}

// 确认对话框
function confirmAction(message) {
    return confirm(message);
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('初中数学错题本应用已加载');
});


/**
 * 标签选择组件
 * 支持多选、搜索、新建标签
 */
class TagSelector {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`找不到容器: ${containerId}`);
            return;
        }

        this.options = {
            placeholder: '选择或输入标签...',
            maxTags: 10,
            allowCreate: true,
            onChange: null,
            ...options
        };

        this.selectedTags = new Set();
        this.allTags = [];
        this.init();
    }

    async init() {
        // 获取所有标签
        try {
            const response = await fetch('/tags/api/list');
            const data = await response.json();
            this.allTags = data;
        } catch (error) {
            console.error('获取标签失败:', error);
            this.allTags = [];
        }

        this.render();
        this.attachEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="tag-selector">
                <div class="tag-selector-selected" id="${this.container.id}-selected"></div>
                <div class="tag-selector-input-wrapper">
                    <input type="text"
                           class="tag-selector-input"
                           id="${this.container.id}-input"
                           placeholder="${this.options.placeholder}">
                    <div class="tag-selector-dropdown" id="${this.container.id}-dropdown"></div>
                </div>
            </div>
        `;

        this.inputEl = this.container.querySelector('.tag-selector-input');
        this.dropdownEl = this.container.querySelector('.tag-selector-dropdown');
        this.selectedEl = this.container.querySelector('.tag-selector-selected');
    }

    attachEvents() {
        // 输入框聚焦时显示下拉列表
        this.inputEl.addEventListener('focus', () => {
            this.showDropdown();
        });

        // 点击下拉框时阻止 input 失焦，避免 blur 提前隐藏下拉框
        this.dropdownEl.addEventListener('mousedown', (e) => {
            e.preventDefault();
        });

        // 输入框失焦时隐藏下拉框
        this.inputEl.addEventListener('blur', () => {
            this.hideDropdown();
        });

        // 输入时过滤标签
        this.inputEl.addEventListener('input', (e) => {
            this.filterTags(e.target.value);
        });

        // 回车键创建新标签
        this.inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const value = this.inputEl.value.trim();
                if (value && this.options.allowCreate) {
                    this.createAndAddTag(value);
                }
            }
        });
    }

    showDropdown() {
        this.filterTags(this.inputEl.value);
        this.dropdownEl.style.display = 'block';
    }

    hideDropdown() {
        this.dropdownEl.style.display = 'none';
    }

    filterTags(query) {
        const filtered = this.allTags.filter(tag =>
            !this.selectedTags.has(tag.id) &&
            tag.name.toLowerCase().includes(query.toLowerCase())
        );

        if (filtered.length === 0 && query.trim() && this.options.allowCreate) {
            this.dropdownEl.innerHTML = `
                <div class="tag-dropdown-item tag-create-new" data-create="${query}">
                    <span>+ 创建标签 "${query}"</span>
                </div>
            `;
        } else {
            this.dropdownEl.innerHTML = filtered.map(tag => `
                <div class="tag-dropdown-item" data-tag-id="${tag.id}">
                    <span class="tag-color-dot" style="background-color: ${tag.color}"></span>
                    <span>${tag.name}</span>
                </div>
            `).join('');
        }

        // 绑定点击事件
        this.dropdownEl.querySelectorAll('.tag-dropdown-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const tagId = item.dataset.tagId;
                const createName = item.dataset.create;

                if (createName) {
                    this.createAndAddTag(createName);
                } else if (tagId) {
                    this.addTag(parseInt(tagId));
                }
            });
        });
    }

    async createAndAddTag(name) {
        try {
            // 生成随机颜色
            const colors = [
                '#0078D4', '#107C10', '#D83B01', '#5C2D91', '#008272', '#CA5010', '#E3008C',
                '#00B7C3', '#8764B8', '#E74856', '#FFB900', '#00CC6A', '#FF8C00', '#68768A'
            ];
            const randomColor = colors[Math.floor(Math.random() * colors.length)];

            const response = await fetch('/tags/api/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, color: randomColor })
            });

            const result = await response.json();
            if (result.success) {
                this.allTags.push(result.tag);
                this.addTag(result.tag.id);
                showToast(`标签 "${name}" 已创建`, 'success');
            } else {
                showToast(result.message || '创建标签失败', 'error');
            }
        } catch (error) {
            console.error('创建标签失败:', error);
            showToast('创建标签失败', 'error');
        }
    }

    addTag(tagId) {
        if (this.selectedTags.size >= this.options.maxTags) {
            showToast(`最多只能选择 ${this.options.maxTags} 个标签`, 'info');
            return;
        }

        const tag = this.allTags.find(t => t.id === tagId);
        if (!tag) return;

        this.selectedTags.add(tagId);
        this.renderSelected();
        this.inputEl.value = '';
        this.filterTags('');

        if (this.options.onChange) {
            this.options.onChange(Array.from(this.selectedTags));
        }
    }

    removeTag(tagId) {
        this.selectedTags.delete(tagId);
        this.renderSelected();

        if (this.options.onChange) {
            this.options.onChange(Array.from(this.selectedTags));
        }
    }

    renderSelected() {
        const tags = Array.from(this.selectedTags).map(id => {
            const tag = this.allTags.find(t => t.id === id);
            return tag ? `
                <span class="tag-selected-item" style="background-color: ${tag.color}">
                    ${tag.name}
                    <span class="tag-remove" data-tag-id="${tag.id}">×</span>
                </span>
            ` : '';
        }).join('');

        this.selectedEl.innerHTML = tags;

        // 绑定删除事件
        this.selectedEl.querySelectorAll('.tag-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const tagId = parseInt(btn.dataset.tagId);
                this.removeTag(tagId);
            });
        });
    }

    getSelectedTags() {
        return Array.from(this.selectedTags);
    }

    setSelectedTags(tagIds) {
        this.selectedTags = new Set(tagIds);
        this.renderSelected();
    }

    clear() {
        this.selectedTags.clear();
        this.renderSelected();
    }
}
