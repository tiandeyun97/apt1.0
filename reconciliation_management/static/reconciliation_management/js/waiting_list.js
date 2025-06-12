/**
 * 等待对账页面脚本
 */

// DOM 加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化填写FB消耗按钮事件
    initAddFbButtons();
    
    // 初始化刷新按钮
    initRefreshButton();
    
    // 初始化导出Excel按钮
    initExportButton();
    
    // 初始化图片预览功能
    initImagePreview();
});

/**
 * 初始化图片预览功能
 */
function initImagePreview() {
    const fileInput = document.getElementById('consumption-attachment');
    const previewButton = document.getElementById('preview-attachment');
    const previewContainer = document.getElementById('attachment-preview-container');
    const previewImg = document.getElementById('attachment-preview');
    const closePreviewButton = document.getElementById('close-preview');
    const attachmentInfo = document.getElementById('attachment-info');
    
    if (!fileInput || !previewButton || !previewContainer || !previewImg) {
        return;
    }
    
    // 预览按钮点击事件
    previewButton.addEventListener('click', function() {
        if (fileInput.files && fileInput.files[0]) {
            const file = fileInput.files[0];
            
            // 检查文件类型
            if (!file.type.match('image/jpeg') && !file.type.match('image/png')) {
                alert('请选择JPG或PNG格式的图片');
                return;
            }
            
            // 显示图片信息
            const fileSize = Math.round(file.size / 1024); // KB
            attachmentInfo.textContent = `${file.name} (${fileSize} KB)`;
            
            // 使用FileReader预览图片
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImg.src = e.target.result;
                previewContainer.classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        } else {
            alert('请先选择图片');
        }
    });
    
    // 关闭预览按钮点击事件
    if (closePreviewButton) {
        closePreviewButton.addEventListener('click', function() {
            previewContainer.classList.add('d-none');
        });
    }
    
    // 文件选择改变时自动预览
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const file = this.files[0];
            
            // 检查文件类型
            if (!file.type.match('image/jpeg') && !file.type.match('image/png')) {
                alert('请选择JPG或PNG格式的图片');
                return;
            }
            
            // 显示图片信息
            const fileSize = Math.round(file.size / 1024); // KB
            attachmentInfo.textContent = `${file.name} (${fileSize} KB)`;
            
            // 压缩图片（如果超过1MB）
            if (file.size > 1024 * 1024) {
                compressImage(file, function(compressedFile) {
                    // 更新文件信息
                    const compressedSize = Math.round(compressedFile.size / 1024); // KB
                    attachmentInfo.textContent = `${file.name} (压缩前: ${fileSize} KB, 压缩后: ${compressedSize} KB)`;
                    
                    // 预览压缩后的图片
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        previewImg.src = e.target.result;
                        previewContainer.classList.remove('d-none');
                    };
                    reader.readAsDataURL(compressedFile);
                    
                    // 替换文件输入框中的文件（注：这一步在实际中无法直接替换，需要其他处理）
                    // 我们将压缩后的文件保存在window对象中，供后续使用
                    window.compressedAttachment = compressedFile;
                });
            } else {
                // 如果文件较小，直接预览
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    previewContainer.classList.remove('d-none');
                };
                reader.readAsDataURL(file);
            }
        }
    });
}

/**
 * 压缩图片
 * @param {File} file 原始图片文件
 * @param {Function} callback 回调函数，参数为压缩后的文件
 */
function compressImage(file, callback) {
    const maxWidth = 1600; // 最大宽度
    const maxHeight = 1200; // 最大高度
    const quality = 0.7; // 压缩质量
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            // 计算新尺寸
            let width = img.width;
            let height = img.height;
            
            if (width > maxWidth) {
                height = Math.round(height * maxWidth / width);
                width = maxWidth;
            }
            
            if (height > maxHeight) {
                width = Math.round(width * maxHeight / height);
                height = maxHeight;
            }
            
            // 创建Canvas并绘制
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);
            
            // 转换为Blob
            canvas.toBlob(function(blob) {
                // 创建新的File对象
                const compressedFile = new File([blob], file.name, {
                    type: file.type,
                    lastModified: Date.now()
                });
                
                callback(compressedFile);
            }, file.type, quality);
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

/**
 * 初始化填写FB消耗按钮事件
 */
function initAddFbButtons() {
    const addFbButtons = document.querySelectorAll('.btn-add-fb');
    const fbConsumptionModal = new bootstrap.Modal(document.getElementById('fbConsumptionModal'));
    const saveButton = document.getElementById('save-fb-consumption');
    
    addFbButtons.forEach(button => {
        button.addEventListener('click', function() {
            const recordId = this.getAttribute('data-id');
            const row = this.closest('tr');
            const taskName = row.querySelector('.task-name').textContent.trim();
            const actualConsumption = row.querySelectorAll('td')[4].textContent.trim();
            
            // 填充模态框数据
            document.getElementById('record-id').value = recordId;
            document.getElementById('task-name').textContent = taskName;
            document.getElementById('actual-consumption').textContent = actualConsumption;
            document.getElementById('fb-consumption').value = '';
            document.getElementById('consumption-note').value = '';
            
            // 重置文件输入
            const fileInput = document.getElementById('consumption-attachment');
            if (fileInput) {
                fileInput.value = '';
            }
            
            // 隐藏预览
            const previewContainer = document.getElementById('attachment-preview-container');
            if (previewContainer) {
                previewContainer.classList.add('d-none');
            }
            
            // 清除压缩文件缓存
            if (window.compressedAttachment) {
                delete window.compressedAttachment;
            }
            
            // 显示模态框
            fbConsumptionModal.show();
        });
    });
    
    // 保存FB消耗按钮事件
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            const form = document.getElementById('fb-consumption-form');
            const recordId = document.getElementById('record-id').value;
            const fbConsumption = document.getElementById('fb-consumption').value;
            const note = document.getElementById('consumption-note').value;
            const fileInput = document.getElementById('consumption-attachment');
            
            // 表单验证
            if (!fbConsumption) {
                alert('请输入FB消耗');
                return;
            }
            
            if (!fileInput.files.length && !window.compressedAttachment) {
                alert('请上传消耗凭证');
                return;
            }
            
            // 使用FormData对象处理表单数据
            const formData = new FormData();
            formData.append('fb_consumption', fbConsumption);
            formData.append('note', note);
            formData.append('redirect_to', 'waiting');
            
            // 添加文件，优先使用压缩后的文件
            if (window.compressedAttachment) {
                formData.append('attachment_file', window.compressedAttachment);
            } else {
                formData.append('attachment_file', fileInput.files[0]);
            }
            
            // 发送更新请求
            saveFbConsumptionWithAttachment(recordId, formData, () => {
                fbConsumptionModal.hide();
                window.location.reload();
            });
        });
    }
}

/**
 * 保存FB消耗和附件
 * @param {string} recordId 记录ID
 * @param {FormData} formData 表单数据
 * @param {Function} callback 回调函数
 */
function saveFbConsumptionWithAttachment(recordId, formData, callback) {
    // 获取CSRF令牌
    const csrfToken = getCsrfToken();
    
    // 发送AJAX请求
    fetch(`/reconciliation/record/${recordId}/update/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.ok) {
            callback();
        } else {
            alert('更新FB消耗失败，请重试');
        }
    })
    .catch(error => {
        console.error('更新FB消耗出错:', error);
        alert('更新FB消耗时出错，请稍后重试');
    });
}

/**
 * 初始化刷新按钮
 */
function initRefreshButton() {
    const refreshButton = document.getElementById('btn-refresh');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            window.location.reload();
        });
    }
}

/**
 * 初始化导出Excel按钮
 */
function initExportButton() {
    const exportButton = document.getElementById('btn-export-excel');
    if (exportButton) {
        exportButton.addEventListener('click', function() {
            const year = document.getElementById('year-select').value;
            const month = document.getElementById('month-select').value;
            const project = document.getElementById('project-select')?.value || '';
            
            // 获取当前页面的状态（等待对账、异常对账或完成对账）
            let status = 'waiting';
            if (window.location.href.includes('exception')) {
                status = 'exception';
            } else if (window.location.href.includes('completed')) {
                status = 'completed';
            }
            
            // 构建导出URL
            let url = `/reconciliation/export/?year=${year}&month=${month}&status=${status}`;
            if (project) {
                url += `&project=${project}`;
            }
            
            window.open(url, '_blank');
        });
    }
}

/**
 * 获取CSRF令牌
 * @returns {string} CSRF令牌
 */
function getCsrfToken() {
    // 从cookie中获取CSRF令牌
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
} 