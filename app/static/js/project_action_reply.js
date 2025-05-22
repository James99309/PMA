// 检查jQuery是否可用，如果不可用则等待加载
(function() {
  // 跟踪已经初始化过的实例，避免重复初始化
  var initializedSystem = false;
  
  function initReplySystem() {
    if (initializedSystem) {
      return;
    }
    
    initializedSystem = true;
    
    $(function() {
        // 根据当前页面URL判断使用哪个路径前缀
        function getActionBaseUrl() {
            // 如果当前URL包含'/customer/'，使用客户模块API，否则使用项目模块API
            if (window.location.pathname.includes('/customer/')) {
                return '/customer/action/';
            } else {
                return '/project/action/';
            }
        }

        // 展开/收起回复
        $(document).off('click', '.reply-toggle-btn').on('click', '.reply-toggle-btn', function() {
            var actionId = $(this).data('action-id');
            var container = $('#replies-' + actionId);
            if (container.is(':empty')) {
                loadReplies(actionId, container);
                $(this).text('收起');
            } else {
                container.empty();
                $(this).text('展开');
            }
        });

        // 显示主回复输入框
        $(document).off('click', '.show-reply-form-btn').on('click', '.show-reply-form-btn', function() {
            var actionId = $(this).data('action-id');
            var formSelector = '#reply-form-' + actionId;
            const form = $(formSelector);
            
            // 检查表单是否存在
            if (form.length === 0) {
                return;
            }
            
            // 使用更直接的方式强制显示，覆盖任何可能的CSS冲突
            if (form.css('display') === 'none') {
                form.css('display', 'block');
                // 双重保险，延迟再检查一次
                setTimeout(function() {
                    if (form.css('display') !== 'block') {
                        form.attr('style', 'display: block !important');
                    }
                }, 50);
            } else {
                form.css('display', 'none');
            }
        });

        // 取消回复（主回复和子回复都支持）
        $(document).off('click', '.cancel-reply').on('click', '.cancel-reply', function() {
            $(this).closest('.reply-form, .child-reply-form').hide();
            $(this).siblings('textarea').val('');
        });

        // 提交主回复
        $(document).off('click', '.submit-reply').on('click', '.submit-reply', function() {
            var form = $(this).closest('.reply-form');
            var actionId = form.attr('id').split('-')[2];
            var content = form.find('textarea').val();
            if (!content.trim()) return;
            $.ajax({
                url: getActionBaseUrl() + actionId + '/reply',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({content: content}),
                headers: {
                    'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
                },
                success: function() {
                    loadReplies(actionId, $('#replies-' + actionId));
                    form.hide();
                    form.find('textarea').val('');
                    // 更新展开/收起按钮的文字
                    $('.reply-toggle-btn[data-action-id="' + actionId + '"]').text('收起');
                },
                error: function(xhr, status, error) {
                    alert('提交回复失败: ' + error);
                }
            });
        });

        // 显示子回复输入框
        $(document).off('click', '.reply-child-btn').on('click', '.reply-child-btn', function() {
            var replyId = $(this).data('reply-id');
            $('#child-reply-form-' + replyId).toggle();
        });

        // 提交子回复
        $(document).off('click', '.submit-child-reply').on('click', '.submit-child-reply', function() {
            var form = $(this).closest('.child-reply-form');
            var replyId = form.attr('id').split('-')[3];
            var actionId = form.data('action-id');
            var content = form.find('textarea').val();
            if (!content.trim()) return;
            $.ajax({
                url: getActionBaseUrl() + actionId + '/reply',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({content: content, parent_reply_id: replyId}),
                headers: {
                    'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
                },
                success: function() {
                    loadReplies(actionId, $('#replies-' + actionId));
                    form.hide();
                    form.find('textarea').val('');
                    // 更新展开/收起按钮的文字
                    $('.reply-toggle-btn[data-action-id="' + actionId + '"]').text('收起');
                },
                error: function(xhr, status, error) {
                    alert('提交回复失败: ' + error);
                }
            });
        });

        // 加载回复树
        function loadReplies(actionId, container) {
            $.get(getActionBaseUrl() + actionId + '/replies', function(data) {
                container.html(renderReplies(data, 0, actionId));
                // 动态内容加载后，手动重新绑定回复相关事件
                rebindDynamicEvents();
                
                // 调用客户详情页面注册的全局重新绑定函数（如果存在）
                if (typeof window.reInitCustomerReplyButtons === 'function') {
                    setTimeout(function() {
                        window.reInitCustomerReplyButtons();
                    }, 100);
                }
            }).fail(function(xhr, status, error) {
                container.html('<div class="alert alert-danger">加载回复失败</div>');
            });
        }

        // 重新绑定动态生成内容的事件
        function rebindDynamicEvents() {
            // 为新生成的子回复按钮重新绑定事件
            $('.reply-child-btn').each(function() {
                var btn = $(this);
                var replyId = btn.data('reply-id');
                
                btn.off('click').on('click', function(e) {
                    e.preventDefault();
                    var formSelector = '#child-reply-form-' + replyId;
                    var form = $(formSelector);
                    if(form.length) {
                        form.toggle();
                    }
                    return false;
                });
            });
            
            // 绑定删除回复按钮
            $('.reply-delete').each(function() {
                var btn = $(this);
                var replyId = btn.data('reply-id');
                
                btn.off('click').on('click', function() {
                    if(confirm('确定要删除这条回复吗？')) {
                        var $this = $(this);
                        $.ajax({
                            url: getActionBaseUrl() + 'reply/' + replyId + '/delete',
                            type: 'POST',
                            headers: {
                                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
                            },
                            success: function(res) {
                                // 直接刷新回复列表，无需二次确认
                                var container = $this.closest('.replies-container');
                                var actionId = container.attr('id').split('-')[1];
                                loadReplies(actionId, container);
                            },
                            error: function() { 
                                alert('删除失败，请重试'); 
                            }
                        });
                    }
                });
            });
        }

        // 递归渲染回复树
        function renderReplies(replies, level, actionId) {
            let html = '';
            replies.forEach(function(reply) {
                html += `<div class="reply" style="margin-left:${level*24}px; border-left:1px solid #eee; padding-left:8px; margin-top:6px;">
                    <div>
                        <span class="fw-bold">${reply.owner}</span>
                        <span class="text-muted small ms-2">${reply.created_at}</span>`;
                if (reply.can_delete) {
                    html += `<span class="reply-delete text-danger" data-reply-id="${reply.id}" style="cursor:pointer;margin-left:8px;">删除</span>`;
                }
                html += `</div>
                    <div class="mb-1">${escapeHtml(reply.content)}</div>
                    <button class="btn btn-link btn-xs reply-child-btn" data-reply-id="${reply.id}">回复</button>
                    <div class="child-reply-form mt-2" id="child-reply-form-${reply.id}" data-action-id="${actionId}" style="display:none">
                        <textarea class="form-control mb-2" rows="2" placeholder="输入回复内容..."></textarea>
                        <button class="btn btn-primary btn-sm submit-child-reply">提交</button>
                        <button class="btn btn-secondary btn-sm cancel-reply">取消</button>
                    </div>
                </div>`;
                if (reply.children && reply.children.length > 0) {
                    html += renderReplies(reply.children, level+1, actionId);
                }
            });
            return html;
        }

        // HTML转义
        function escapeHtml(text) {
            return $('<div/>').text(text).html();
        }

        // 绑定删除事件 - 已移到rebindDynamicEvents中处理
        $(document).off('click', '.reply-delete')
    });
  }

  // 等待jQuery加载
  function checkJQuery() {
    if (window.jQuery) {
      // jQuery加载完成，初始化回复系统
      initReplySystem();
    } else {
      // jQuery还没加载，等待100ms后重试
      setTimeout(checkJQuery, 100);
    }
  }
  
  // 开始检查
  checkJQuery();
})(); 