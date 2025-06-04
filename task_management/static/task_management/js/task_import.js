document.addEventListener('DOMContentLoaded', function() {
    // DOM元素
    const uploadArea = document.getElementById('uploadArea');
    const taskFile = document.getElementById('taskFile');
    const fileName = document.getElementById('fileName');
    const fileNameText = document.getElementById('fileNameText');
    const uploadButton = document.getElementById('uploadButton');
    const uploadForm = document.getElementById('uploadForm');
    const progressContainer = document.getElementById('progressContainer');
    const importProgress = document.getElementById('importProgress');
    const progressStatus = document.getElementById('progressStatus');
    const progressStats = document.getElementById('progressStats');
    const importResult = document.getElementById('importResult');
    const successAlert = document.getElementById('successAlert');
    const skipAlert = document.getElementById('skipAlert');
    const errorAlert = document.getElementById('errorAlert');
    const successMessage = document.getElementById('successMessage');
    const skipMessage = document.getElementById('skipMessage');
    const errorMessage = document.getElementById('errorMessage');
    const errorList = document.getElementById('errorList');
    
    // 处理文件选择
    taskFile.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            displayFileName(this.files[0].name);
        }
    });
    
    // 拖放功能
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', function() {
        this.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
        
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            taskFile.files = e.dataTransfer.files;
            displayFileName(e.dataTransfer.files[0].name);
        }
    });
    
    // 点击上传区域触发文件选择
    uploadArea.addEventListener('click', function(e) {
        // 阻止事件冒泡，避免触发两次点击
        e.stopPropagation();
        // 只有在点击的是上传区域而不是其子元素时才触发文件选择
        if (e.target === uploadArea || uploadArea.contains(e.target)) {
            // 确保taskFile元素存在且没有被禁用
            if (taskFile && !taskFile.disabled) {
                taskFile.click();
            }
        }
    });
    
    // 显示文件名
    function displayFileName(name) {
        // 确保有文件名才显示
        if (name) {
            fileNameText.textContent = name;
            fileName.style.display = 'flex';
            uploadButton.style.display = 'inline-block';
            // 重置进度区域
            resetProgress();
        }
    }
    
    // 导入按钮点击事件
    uploadButton.addEventListener('click', function(e) {
        e.preventDefault(); // 阻止表单默认提交
        if (!taskFile.files || !taskFile.files[0]) {
            alert('请选择要上传的Excel文件');
            return;
        }
        
        // 开始导入流程
        startImport();
    });
    
    // 重置进度条和结果显示
    function resetProgress() {
        // 隐藏进度和结果区域
        progressContainer.style.display = 'none';
        importResult.style.display = 'none';
        
        // 重置进度条
        updateProgress(0, '正在准备导入...');
        progressStats.innerHTML = '';
        
        // 重置结果显示
        successAlert.style.display = 'none';
        skipAlert.style.display = 'none';
        errorAlert.style.display = 'none';
        errorList.style.display = 'none';
        errorList.innerHTML = '';
    }
    
    // 更新进度条
    function updateProgress(percent, statusText) {
        importProgress.style.width = percent + '%';
        importProgress.setAttribute('aria-valuenow', percent);
        importProgress.textContent = percent + '%';
        
        if (statusText) {
            progressStatus.textContent = statusText;
        }
    }
    
    // 开始导入流程
    function startImport() {
        // 显示进度区域
        resetProgress();
        progressContainer.style.display = 'block';
        
        // 禁用上传按钮
        uploadButton.disabled = true;
        uploadButton.innerHTML = '<i class="bi bi-hourglass-split"></i> 导入中...';
        
        // 准备表单数据
        const formData = new FormData(uploadForm);
        formData.append('task_file', taskFile.files[0]);
        
        // 获取用户选择的处理重复数据的方式
        const duplicateAction = document.querySelector('input[name="duplicate_action"]:checked').value;
        formData.append('duplicate_action', duplicateAction);
        
        // 创建XMLHttpRequest对象
        const xhr = new XMLHttpRequest();
        
        // 监听进度更新
        let pollInterval;
        
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                clearInterval(pollInterval);
                
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        handleImportResponse(response);
                    } catch (e) {
                        console.error('解析响应失败:', e);
                        showError('服务器响应格式错误，请联系管理员');
                    }
                } else {
                    showError('导入失败: 服务器错误 (' + xhr.status + ')');
                }
                
                // 恢复上传按钮状态
                uploadButton.disabled = false;
                uploadButton.innerHTML = '<i class="bi bi-cloud-upload"></i> 导入';
            }
        };
        
        // 错误处理
        xhr.onerror = function() {
            clearInterval(pollInterval);
            showError('网络错误，请检查您的网络连接');
            uploadButton.disabled = false;
            uploadButton.innerHTML = '<i class="bi bi-cloud-upload"></i> 导入';
        };
        
        // 发送请求
        xhr.open('POST', '/task_management/import/', true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        xhr.send(formData);
        
        // 更新初始状态
        updateProgress(5, '开始处理Excel文件...');
        
        // 为了UX体验，设置一个模拟的进度更新（10%到60%）
        let simulatedProgress = 10;
        pollInterval = setInterval(function() {
            // 只有在没有收到服务器进度更新时才使用模拟进度
            if (simulatedProgress < 60) {
                simulatedProgress += 2;
                updateProgress(simulatedProgress, '正在处理Excel数据...');
                
                if (simulatedProgress >= 60) {
                    clearInterval(pollInterval);
                }
            }
        }, 300);
    }
    
    // 处理导入响应
    function handleImportResponse(response) {
        // 检查状态
        if (response.status === 'error') {
            showError(response.message);
            return;
        }
        
        if (response.status === 'complete') {
            // 完成导入，显示结果
            updateProgress(100, '导入完成');
            
            // 更新统计信息
            const totalText = `总共处理: ${response.total} 条记录`;
            const successText = `成功导入: ${response.success} 条记录`;
            const updateText = `成功更新: ${response.update} 条记录`;
            const skipText = `跳过处理: ${response.skip} 条记录`;
            const errorText = `导入失败: ${response.error} 条记录`;
            
            progressStats.innerHTML = `
                <div class="stats-row">${totalText}</div>
                <div class="stats-row success">${successText}</div>
                <div class="stats-row update">${updateText}</div>
                <div class="stats-row skip">${skipText}</div>
                <div class="stats-row error">${errorText}</div>
            `;
            
            // 显示详细结果
            importResult.style.display = 'block';
            
            // 成功消息
            if (response.success > 0 && response.success_message) {
                successAlert.style.display = 'block';
                successMessage.textContent = response.success_message;
            }
            
            // 更新消息
            if (response.update > 0 && response.update_message) {
                skipAlert.style.display = 'block';
                skipMessage.textContent = response.update_message;
            }
            
            // 跳过消息
            if (response.skip > 0 && response.skip_message) {
                const skipDiv = document.createElement('div');
                skipDiv.className = 'alert alert-warning alert-dismissible fade show';
                skipDiv.role = 'alert';
                skipDiv.innerHTML = `
                    <i class="bi bi-arrow-right-circle me-2"></i>
                    ${response.skip_message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                importResult.appendChild(skipDiv);
            }
            
            // 错误消息
            if (response.error > 0 && response.error_message) {
                errorAlert.style.display = 'block';
                errorMessage.textContent = response.error_message;
                
                // 如果有错误详情，显示列表
                if (response.error_detail && response.error_detail.length > 0) {
                    errorList.style.display = 'block';
                    response.error_detail.forEach(function(error) {
                        const li = document.createElement('li');
                        li.textContent = error;
                        errorList.appendChild(li);
                    });
                }
            }
            
            // 如果所有记录都成功或更新，3秒后自动跳转到任务列表
            if (response.error === 0) {
                setTimeout(function() {
                    window.location.href = '/task_management/';
                }, 3000);
            }
        }
    }
    
    // 显示错误消息
    function showError(message) {
        updateProgress(100, '导入失败');
        importResult.style.display = 'block';
        errorAlert.style.display = 'block';
        errorMessage.textContent = message;
    }
}); 