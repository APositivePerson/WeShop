/**
 * 微信小店AI上架助手 - 前端逻辑
 * 增强版：支持微信登录、店铺管理和权限验证
 */

// API基础URL
const API_BASE = window.location.origin;

// 当前生成的数据
let currentProductData = null;

// 模板数据
const templates = {
    'ins风手机壳': '上架一个ins风手机壳，适用于iPhone15，售价39元，库存200',
    '可爱耳机': '可爱风无线蓝牙耳机，粉色少女系，支持降噪，售价99元',
    '极简T恤': '极简风纯棉白色T恤，男女同款，舒适透气，售价69元',
    '商务背包': '商务风双肩包，大容量防水，适合通勤出差，售价198元',
};

// ============ 认证相关 ============

/**
 * 获取认证头
 */
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token || ''
    };
}

/**
 * 检查是否已登录
 */
function isLoggedIn() {
    return !!localStorage.getItem('token');
}

/**
 * 处理API错误
 */
function handleApiError(response, defaultMessage) {
    if (response.status === 401) {
        showToast('登录已过期，请重新登录', 'error');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setTimeout(() => {
            window.location.href = '/login';
        }, 1500);
        return true;
    }
    if (response.status === 403) {
        showToast('没有操作权限', 'error');
        return true;
    }
    return false;
}

// ============ 商品生成相关 ============

/**
 * 填充模板
 */
function fillTemplate(key) {
    const textarea = document.getElementById('productInput');
    textarea.value = templates[key];
    textarea.focus();
}

/**
 * 生成商品
 */
async function generateProduct() {
    const input = document.getElementById('productInput').value.trim();
    
    if (!input) {
        showToast('请输入商品描述', 'error');
        return;
    }
    
    if (input.length < 5) {
        showToast('描述太短，请提供更多商品信息', 'error');
        return;
    }
    
    // 显示加载
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ description: input }),
        });
        
        if (handleApiError(response, '生成失败')) {
            showLoading(false);
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            currentProductData = data;
            renderResults(data);
            showResultSection(true);
            showToast('生成成功！', 'success');
        } else {
            showToast(data.message || '生成失败', 'error');
        }
    } catch (error) {
        console.error('生成失败:', error);
        showToast('网络错误，请稍后重试', 'error');
    } finally {
        showLoading(false);
    }
}

/**
 * 渲染结果
 */
function renderResults(data) {
    const content = data.optimized_content;
    const info = data.product_info;
    
    // 优化标题
    document.getElementById('titleText').textContent = content.title;
    
    // 卖点列表
    const sellingList = document.getElementById('sellingPoints');
    sellingList.innerHTML = content.selling_points.map(point => `
        <li>
            <span class="selling-icon">${point.icon}</span>
            <div>
                <div class="selling-title">${point.title}</div>
                <div class="selling-desc">${point.desc}</div>
            </div>
        </li>
    `).join('');
    
    // 商品标签
    const tagsList = document.getElementById('tagsList');
    tagsList.innerHTML = content.tags.map(tag => `
        <span class="tag">${tag}</span>
    `).join('');
    
    // 详情页文案
    document.getElementById('detailContent').textContent = content.detail_content;
    
    // 主图文案建议
    const imageSuggestions = document.getElementById('imageSuggestions');
    imageSuggestions.innerHTML = content.main_image_suggestions.map(img => `
        <div class="image-item">
            <span class="image-num">${img.image_number}</span>
            <div class="image-type">${img.type}</div>
            <div class="image-scene">${img.scene}</div>
            <div class="image-text">"${img.text_overlay}"</div>
        </div>
    `).join('');
    
    // 商品信息
    const productInfo = document.getElementById('productInfo');
    productInfo.innerHTML = `
        <div class="info-item">
            <span class="info-label">商品名称</span>
            <span class="info-value">${info.product_name || '-'}</span>
        </div>
        <div class="info-item">
            <span class="info-label">风格</span>
            <span class="info-value">${info.style || '-'}</span>
        </div>
        <div class="info-item">
            <span class="info-label">品类</span>
            <span class="info-value">${info.category || '-'}</span>
        </div>
        <div class="info-item">
            <span class="info-label">价格</span>
            <span class="info-value">${info.price ? '¥' + info.price : '-'}</span>
        </div>
        <div class="info-item">
            <span class="info-label">库存</span>
            <span class="info-value">${info.stock || '-'}</span>
        </div>
        <div class="info-item">
            <span class="info-label">适用型号</span>
            <span class="info-value">${info.specs?.model || '-'}</span>
        </div>
    `;
}

/**
 * 重新生成
 */
async function regenerate() {
    const input = document.getElementById('productInput').value.trim();
    if (!input) return;
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/regenerate`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ description: input }),
        });
        
        if (handleApiError(response, '重新生成失败')) {
            showLoading(false);
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            currentProductData = data;
            renderResults(data);
            showToast('重新生成成功！', 'success');
        }
    } catch (error) {
        console.error('重新生成失败:', error);
        showToast('重新生成失败', 'error');
    } finally {
        showLoading(false);
    }
}

/**
 * 一键上架
 */
async function publishProduct() {
    if (!currentProductData) {
        showToast('请先生成商品内容', 'error');
        return;
    }
    
    // 获取当前选中的店铺
    const shopSelect = document.getElementById('shopSelect');
    const shopId = shopSelect ? shopSelect.value : null;
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/publish`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                product_info: currentProductData.product_info,
                content: currentProductData.optimized_content,
                images: [],
                shop_id: shopId
            }),
        });
        
        if (handleApiError(response, '上架失败')) {
            showLoading(false);
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`上架成功！商品ID: ${data.product_id}`, 'success');
            // 保存成功后刷新商品列表
            loadMyProducts();
        } else {
            // 处理权限错误
            if (data.message && data.message.includes('权限')) {
                showToast(data.message, 'error');
            } else {
                showToast(data.message || '上架失败', 'error');
            }
        }
    } catch (error) {
        console.error('上架失败:', error);
        showToast('上架失败，请检查网络', 'error');
    } finally {
        showLoading(false);
    }
}

// ============ 商品管理相关 ============

/**
 * 加载我的商品列表
 */
async function loadMyProducts() {
    const shopSelect = document.getElementById('shopSelectProducts');
    const shopId = shopSelect ? shopSelect.value : '';
    
    const url = shopId 
        ? `${API_BASE}/api/products?shop_id=${shopId}` 
        : `${API_BASE}/api/products`;
    
    try {
        const response = await fetch(url, {
            headers: getAuthHeaders()
        });
        
        if (handleApiError(response, '加载商品列表失败')) {
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            renderMyProducts(data.products);
        }
    } catch (error) {
        console.error('加载商品列表失败:', error);
        document.getElementById('myProductsList').innerHTML = `
            <div class="empty-state">加载失败，请刷新重试</div>
        `;
    }
}

/**
 * 渲染我的商品列表
 */
function renderMyProducts(products) {
    const container = document.getElementById('myProductsList');
    if (!container) return;
    
    if (products.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无商品，去生成并上架一个吧！</div>';
        return;
    }
    
    container.innerHTML = products.map(p => `
        <div class="product-item">
            <div class="product-info">
                <h4>${p.title}</h4>
                <p>价格: ¥${p.price} | 库存: ${p.stock}</p>
                <span class="status-badge ${p.status === '已上架' ? 'status-online' : 'status-offline'}">${p.status}</span>
            </div>
            <div class="product-actions">
                <button class="btn btn-sm" onclick="deleteProduct('${p.product_id}')">删除</button>
            </div>
        </div>
    `).join('');
}

/**
 * 删除商品
 */
async function deleteProduct(productId) {
    if (!confirm('确定要删除这个商品记录吗？')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/products/${productId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (handleApiError(response, '删除失败')) {
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            showToast('删除成功', 'success');
            loadMyProducts();
        }
    } catch (error) {
        showToast('删除失败', 'error');
    }
}

/**
 * 同步微信小店商品
 */
async function syncProducts() {
    const shopSelect = document.getElementById('shopSelectProducts');
    const shopId = shopSelect ? shopSelect.value : '';
    
    showLoading(true);
    
    try {
        const url = shopId 
            ? `${API_BASE}/api/products/sync?shop_id=${shopId}`
            : `${API_BASE}/api/products/sync`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        
        if (handleApiError(response, '同步失败')) {
            showLoading(false);
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`同步成功，共 ${data.count} 个商品`, 'success');
            loadMyProducts();
        } else {
            showToast(data.error || '同步失败', 'error');
        }
    } catch (error) {
        showToast('同步失败', 'error');
    } finally {
        showLoading(false);
    }
}

// ============ UI工具函数 ============

/**
 * 复制文本
 */
function copyText(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    let text = '';
    
    if (element.tagName === 'UL') {
        // 卖点列表
        text = Array.from(element.querySelectorAll('li')).map(li => {
            const title = li.querySelector('.selling-title')?.textContent || '';
            const desc = li.querySelector('.selling-desc')?.textContent || '';
            return `${title}：${desc}`;
        }).join('\n');
    } else if (elementId === 'tagsList') {
        // 标签
        text = Array.from(element.querySelectorAll('.tag')).map(tag => tag.textContent).join(', ');
    } else {
        text = element.textContent;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败', 'error');
    });
}

/**
 * 显示模板选择
 */
function showTemplates() {
    showToast('点击上方快捷模板即可填充', 'info');
}

/**
 * 显示/隐藏结果区域
 */
function showResultSection(show) {
    const section = document.getElementById('resultSection');
    if (section) {
        section.style.display = show ? 'block' : 'none';
        if (show) {
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

/**
 * 显示/隐藏加载
 */
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

/**
 * 显示提示
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = message;
    toast.className = 'toast show';
    
    if (type === 'error') {
        toast.style.background = '#EF4444';
    } else if (type === 'success') {
        toast.style.background = '#07C160';
    } else {
        toast.style.background = '#333';
    }
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

/**
 * 回车快捷生成
 */
document.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById('productInput');
    if (textarea) {
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.metaKey) {
                generateProduct();
            }
        });
    }
});
