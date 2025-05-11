$(function() {
    // 展开/收起回复
    $(document).on('click', '.reply-toggle-btn', function() {
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
    $(document).on('click', '.show-reply-form-btn', function() {
        var actionId = $(this).data('action-id');
        $('#reply-form-' + actionId).toggle();
    });

    // 取消回复（主回复和子回复都支持）
    $(document).on('click', '.cancel-reply', function() {
        $(this).closest('.reply-form, .child-reply-form').hide();
        $(this).siblings('textarea').val('');
    });

    // 提交主回复
    $(document).on('click', '.submit-reply', function() {
        var form = $(this).closest('.reply-form');
        var actionId = form.attr('id').split('-')[2];
        var content = form.find('textarea').val();
        if (!content.trim()) return;
        $.ajax({
            url: '/project/action/' + actionId + '/reply',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({content: content}),
            success: function() {
                loadReplies(actionId, $('#replies-' + actionId));
                form.hide();
                form.find('textarea').val('');
                // 更新展开/收起按钮的文字
                $('.reply-toggle-btn[data-action-id="' + actionId + '"]').text('收起');
            }
        });
    });

    // 显示子回复输入框
    $(document).on('click', '.reply-child-btn', function() {
        var replyId = $(this).data('reply-id');
        $('#child-reply-form-' + replyId).toggle();
    });

    // 提交子回复
    $(document).on('click', '.submit-child-reply', function() {
        var form = $(this).closest('.child-reply-form');
        var replyId = form.attr('id').split('-')[3];
        var actionId = form.data('action-id');
        var content = form.find('textarea').val();
        if (!content.trim()) return;
        $.ajax({
            url: '/project/action/' + actionId + '/reply',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({content: content, parent_reply_id: replyId}),
            success: function() {
                loadReplies(actionId, $('#replies-' + actionId));
                form.hide();
                form.find('textarea').val('');
                // 更新展开/收起按钮的文字
                $('.reply-toggle-btn[data-action-id="' + actionId + '"]').text('收起');
            }
        });
    });

    // 加载回复树
    function loadReplies(actionId, container) {
        $.get('/project/action/' + actionId + '/replies', function(data) {
            container.html(renderReplies(data, 0, actionId));
        });
    }

    // 递归渲染回复树
    function renderReplies(replies, level, actionId) {
        let html = '';
        replies.forEach(function(reply) {
            html += `<div class="reply" style="margin-left:${level*24}px; border-left:1px solid #eee; padding-left:8px; margin-top:6px;">
                <div>
                    <span class="fw-bold">${reply.owner}</span>
                    <span class="text-muted small ms-2">${reply.created_at}</span>
                </div>
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
}); 