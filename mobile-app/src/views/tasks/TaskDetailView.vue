<!--
  TaskDetailView - Task detail (P1 step 4)
  Pixel port of Claude Design "PMA Task EN" task-detail-en.jsx + quick-status
  / review sheets from task-forms-en.jsx. status/priority text from backend
  *_label; other UI text via t() (i18n rule). Local TK = design task-base.
-->
<template>
  <div :style="{ background: TK.bg, height: '100%', fontFamily: TK.sans, color: TK.ink,
    display: 'flex', flexDirection: 'column' }">
    <div class="status-pad" />
    <!-- nav -->
    <div :style="{ height: '52px', display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', padding: '0 12px', flexShrink: 0,
      borderBottom: `1px solid ${TK.divider}` }">
      <button @click="router.back()" class="active:opacity-60"
        :style="{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'none',
          border: 'none', color: TK.ink2, fontSize: '14px', padding: 0 }">
        <span :style="{ fontSize: '22px', lineHeight: 1, fontWeight: 300 }">‹</span>
        <span>{{ t('task.navTasks') }}</span>
      </button>
      <span :style="{ fontSize: '15px', fontWeight: 600 }">{{ t('task.detailTitle') }}</span>
      <span @click="d?.can_edit && router.push(`/tasks/${id}/edit`)"
        class="active:opacity-60"
        :style="{ minWidth: '40px', textAlign: 'right', fontSize: '13px',
        color: TK.accent, fontWeight: 600 }">{{ d?.can_edit ? t('common.edit') : '' }}</span>
    </div>

    <div v-if="loading" :style="{ flex: 1, display: 'flex', alignItems: 'center',
      justifyContent: 'center', color: TK.ink4 }">···</div>

    <div v-else-if="d" :style="{ flex: 1, overflowY: 'auto', paddingBottom: '92px' }">
      <div :style="{ padding: '14px 20px 18px' }">
        <div :style="{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }">
          <span :style="chip(pri(d.priority), 'md')">{{ d.priority_label }}</span>
          <span :style="chip(stat(d.status), 'md')">{{ d.status_label }}</span>
          <span v-if="d.overdue" :style="{ fontSize: '10px', color: TK.red, fontWeight: 700,
            background: TK.redSoft, padding: '3px 7px', borderRadius: '4px' }">{{ t('task.overdue') }}</span>
        </div>
        <h1 :style="{ margin: 0, fontFamily: 'var(--font-serif)', fontSize: '24px',
          fontWeight: 600, color: TK.ink, lineHeight: 1.25 }">{{ d.title }}</h1>
        <div :style="{ fontSize: '12px', color: TK.ink3, marginTop: '6px' }">
          {{ taskCode }} · {{ t('task.metaCreated') }} {{ fmt(d.created_at) }} · {{ t('task.metaUpdated') }} {{ fmt(d.updated_at) }}
        </div>
      </div>

      <!-- 2x2 meta -->
      <div :style="{ margin: '0 16px 12px', background: TK.card, borderRadius: '12px',
        border: `1px solid ${TK.divider}`, padding: '12px 0', display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)' }">
        <div v-for="(m, i) in metaCells" :key="i" :style="{ padding: '6px 16px',
          borderRight: i % 2 === 0 ? `1px solid ${TK.dividerSoft}` : 'none',
          borderTop: i > 1 ? `1px solid ${TK.dividerSoft}` : 'none' }">
          <div :style="{ fontSize: '10.5px', color: TK.ink3, letterSpacing: '0.4px',
            textTransform: 'uppercase' }">{{ m.l }}</div>
          <div :style="{ fontSize: '14px', fontWeight: 600, marginTop: '3px',
            color: m.accent ? TK.red : TK.ink }">{{ m.v || '—' }}</div>
        </div>
      </div>

      <!-- collaborators — own full-width row, not mixed with the creator -->
      <div v-if="sharedNames" :style="{ margin: '0 16px 12px', background: TK.card,
        borderRadius: '12px', border: `1px solid ${TK.divider}`, padding: '10px 16px' }">
        <div :style="{ fontSize: '10.5px', color: TK.ink3, letterSpacing: '0.4px',
          textTransform: 'uppercase' }">{{ t('task.fShared') }}</div>
        <div :style="{ fontSize: '14px', fontWeight: 600, marginTop: '3px',
          color: TK.ink, lineHeight: 1.5 }">{{ sharedNames }}</div>
      </div>

      <!-- description -->
      <div :style="secTitle">{{ t('task.secDescription') }}</div>
      <div :style="{ background: TK.card, padding: '14px 20px', fontSize: '13.5px',
        color: TK.ink2, lineHeight: 1.65, borderTop: `1px solid ${TK.dividerSoft}`,
        borderBottom: `1px solid ${TK.dividerSoft}` }">
        {{ d.description || t('task.noDescription') }}
      </div>

      <!-- links -->
      <div :style="secTitle">{{ t('task.secLinks') }}</div>
      <div :style="{ background: TK.card, borderTop: `1px solid ${TK.dividerSoft}`,
        borderBottom: `1px solid ${TK.dividerSoft}` }">
        <div v-for="(lk, i) in linkRows" :key="lk.l" :style="{ padding: '12px 20px',
          display: 'flex', gap: '14px', borderBottom: i < linkRows.length - 1 ? `1px solid ${TK.dividerSoft}` : 'none' }">
          <div :style="{ width: '86px', fontSize: '12px', color: TK.ink3, flexShrink: 0 }">{{ lk.l }}</div>
          <div :style="{ flex: 1, fontSize: '13.5px' }">
            <span v-if="lk.v" :style="{ color: TK.accent, fontWeight: 500 }">{{ lk.v }}</span>
            <span v-else :style="{ color: TK.ink4 }">{{ t('task.notLinked') }}</span>
          </div>
        </div>
      </div>

      <!-- reviewers -->
      <template v-if="d.reviewers && d.reviewers.length">
        <div :style="secTitle">{{ t('task.secReviewers') }}</div>
        <div :style="{ background: TK.card, borderTop: `1px solid ${TK.dividerSoft}`,
          borderBottom: `1px solid ${TK.dividerSoft}` }">
          <div v-for="(rv, i) in d.reviewers" :key="i" :style="{ padding: '12px 20px',
            display: 'flex', alignItems: 'center', gap: '12px',
            borderBottom: i < d.reviewers.length - 1 ? `1px solid ${TK.dividerSoft}` : 'none' }">
            <span :style="ava(rv.reviewer_name || rv.name, 32)">{{ shortOf(rv.reviewer_name || rv.name) }}</span>
            <div :style="{ flex: 1, fontSize: '13.5px', fontWeight: 600 }">{{ rv.reviewer_name || rv.name }}</div>
            <span :style="{ fontSize: '11px', fontWeight: 600, padding: '3px 8px', borderRadius: '4px',
              color: rvTone(rv.status).color, background: rvTone(rv.status).bg }">{{ rvLabel(rv.status) }}</span>
          </div>
        </div>
      </template>

      <!-- attachments -->
      <div :style="secTitle">{{ t('task.secAttachments', { n: (d.attachments || []).length }) }}</div>
      <div :style="{ background: TK.card, borderTop: `1px solid ${TK.dividerSoft}`,
        borderBottom: `1px solid ${TK.dividerSoft}` }">
        <div v-for="(a, i) in (d.attachments || [])" :key="a.id"
          :style="{ padding: '12px 20px', display: 'flex', alignItems: 'center', gap: '12px',
            borderBottom: `1px solid ${TK.dividerSoft}` }">
          <span :style="{ width: '30px', height: '30px', borderRadius: '7px', flexShrink: 0,
            background: TK.blueSoft, color: TK.blue, display: 'flex', alignItems: 'center',
            justifyContent: 'center', fontSize: '10px', fontWeight: 700 }">
            {{ extOf(a.filename) }}</span>
          <div :style="{ flex: 1, minWidth: 0 }" @click="openAtt(a)">
            <div :style="{ fontSize: '13.5px', fontWeight: 600, color: TK.ink,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }">{{ a.filename }}</div>
            <div :style="{ fontSize: '11px', color: TK.ink3, marginTop: '2px' }">
              {{ fmtSize(a.file_size) }}<template v-if="a.uploader_name"> · {{ a.uploader_name }}</template></div>
          </div>
          <span v-if="auth.user && a.uploaded_by === auth.user.id" @click="delAtt(a)"
            class="active:opacity-60"
            :style="{ flexShrink: 0, color: TK.red, fontSize: '12px' }">✕</span>
        </div>
        <div @click="pickFile" class="active:opacity-60"
          :style="{ padding: '13px 20px', display: 'flex', alignItems: 'center', gap: '8px',
            color: TK.accent, fontSize: '13px', fontWeight: 600 }">
          <span :style="{ fontSize: '16px', lineHeight: 1 }">＋</span>
          {{ uploading ? t('task.uploading') : t('task.addAttachment') }}
        </div>
        <input ref="fileInput" type="file" style="display:none" @change="onFile" />
      </div>

      <!-- subtasks -->
      <div :style="{ ...secTitle, display: 'flex', alignItems: 'center' }">
        <span :style="{ flex: 1 }">{{ t('task.secSubtasks', { done: subDone, total: (d.subtasks || []).length }) }}</span>
        <span v-if="d.can_subtask" @click="openSubForm(null)" class="active:opacity-60"
          :style="{ color: TK.accent, fontSize: '12px', fontWeight: 600,
            textTransform: 'none', letterSpacing: 0 }">＋ {{ t('task.addSubtask') }}</span>
      </div>
      <div v-if="(d.subtasks || []).length" :style="{ background: TK.card,
        borderTop: `1px solid ${TK.dividerSoft}`, borderBottom: `1px solid ${TK.dividerSoft}` }">
        <div v-for="(s, i) in d.subtasks" :key="s.id"
          @click="openSub(s)" class="active:opacity-60"
          :style="{ padding: '12px 20px',
          display: 'flex', alignItems: 'flex-start', gap: '12px',
          borderBottom: i < d.subtasks.length - 1 ? `1px solid ${TK.dividerSoft}` : 'none' }">
          <span :style="{ width: '20px', height: '20px', flexShrink: 0, marginTop: '1px',
            borderRadius: s.is_milestone ? '4px' : '10px', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            border: `1.5px solid ${s.status === 'completed' ? TK.green : (s.is_milestone ? TK.purple : TK.divider)}`,
            background: s.status === 'completed' ? TK.green : 'transparent', color: '#fff', fontSize: '11px' }">
            <span v-if="s.status === 'completed'">✓</span>
          </span>
          <div :style="{ flex: 1, minWidth: 0 }">
            <div :style="{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }">
              <span :style="{ fontSize: '13.5px', fontWeight: 600,
                textDecoration: s.status === 'completed' ? 'line-through' : 'none',
                opacity: s.status === 'completed' ? 0.55 : 1 }">{{ s.title }}</span>
              <span v-if="s.is_milestone" :style="{ fontSize: '9.5px', color: TK.purple,
                background: TK.purpleSoft, padding: '1px 5px', borderRadius: '3px',
                fontWeight: 700, letterSpacing: '0.4px', textTransform: 'uppercase' }">{{ t('task.milestone') }}</span>
            </div>
            <div :style="{ fontSize: '11px', color: TK.ink3, marginTop: '4px' }">
              {{ s.owner_name }} · {{ s.start }} – {{ s.due }}
              <template v-if="s.progress_notes > 0"> · <span :style="{ color: TK.blue, fontWeight: 600 }">{{ t('task.subUpdates', { n: s.progress_notes }) }}</span></template>
            </div>
          </div>
        </div>
      </div>

      <!-- activity timeline -->
      <div :style="secTitle">{{ t('task.secActivity', { n: commentCount }) }}</div>
      <div :style="{ padding: '0 20px 12px' }">
        <template v-for="(r, i) in (d.timeline || [])" :key="i">
          <div v-if="r.kind === 'system'" :style="{ padding: '8px 0 8px 30px', position: 'relative',
            fontSize: '11px', color: TK.ink3, fontStyle: 'italic', fontFamily: 'var(--font-serif)' }">
            <span :style="{ position: 'absolute', left: '11px', top: '12px', width: '7px',
              height: '7px', borderRadius: '3.5px', background: TK.divider }" />
            {{ r.text }} <span :style="{ color: TK.ink4, fontStyle: 'normal', marginLeft: '6px' }">{{ r.at }}</span>
          </div>
          <div v-else-if="r.kind === 'progress'" :style="{ margin: '4px 0 10px', paddingLeft: '30px' }">
            <div :style="{ background: TK.blueSoft, borderRadius: '8px', padding: '8px 12px',
              border: '1px solid #DCE6F2' }">
              <div :style="{ fontSize: '10px', color: '#1A4A8C', fontWeight: 600,
                letterSpacing: '0.4px', marginBottom: '3px', textTransform: 'uppercase' }">
                {{ t('task.tlUpdate') }}<template v-if="r.sub"> · {{ r.sub }}</template></div>
              <div :style="{ fontSize: '12.5px', color: TK.ink, lineHeight: 1.5 }">{{ r.text }}</div>
              <div :style="{ fontSize: '10px', color: TK.ink3, marginTop: '4px' }">{{ r.author }} · {{ r.at }}</div>
            </div>
          </div>
          <div v-else :style="{ display: 'flex', gap: '10px', padding: '10px 0' }">
            <span :style="ava(r.author, 24)">{{ r.author_short }}</span>
            <div :style="{ flex: 1, minWidth: 0 }">
              <div :style="{ fontSize: '12px', color: TK.ink2, marginBottom: '3px' }">
                <strong :style="{ fontWeight: 600 }">{{ r.author }}</strong>
                <span :style="{ color: TK.ink4, marginLeft: '6px' }">{{ r.at }}</span>
              </div>
              <div :style="{ fontSize: '13.5px', color: TK.ink, lineHeight: 1.55 }">{{ r.text }}</div>
            </div>
          </div>
        </template>
        <div v-if="!(d.timeline || []).length" :style="{ padding: '20px 0', textAlign: 'center',
          fontSize: '12px', color: TK.ink4 }">{{ t('task.noActivity') }}</div>
      </div>
    </div>

    <!-- bottom bar -->
    <div v-if="d" :style="{ position: 'absolute', bottom: 0, left: 0, right: 0,
      padding: '10px 12px calc(22px + env(safe-area-inset-bottom))', background: TK.card,
      borderTop: `1px solid ${TK.divider}`, display: 'flex', gap: '8px', alignItems: 'center' }">
      <template v-if="d.can_review">
        <button @click="openReview('reject')" :style="{ flex: 1, height: '44px', borderRadius: '22px',
          background: TK.card, color: TK.red, border: `1.5px solid ${TK.red}`, fontSize: '14px',
          fontWeight: 600 }">{{ t('task.reject') }}</button>
        <button @click="openReview('approve')" :style="{ flex: 2, height: '44px', borderRadius: '22px',
          background: TK.green, color: '#fff', border: 'none', fontSize: '14px', fontWeight: 600 }">{{ t('task.approve') }}</button>
      </template>
      <template v-else-if="d.can_resubmit">
        <button @click="doResubmit" :style="{ flex: 1, height: '44px', borderRadius: '22px',
          background: TK.purple, color: '#fff', border: 'none', fontSize: '14px',
          fontWeight: 600 }">{{ t('task.resubmitReview') }}</button>
      </template>
      <template v-else>
        <div @click="commentEditorOpen = true"
          :style="{ flex: 1, height: '40px', lineHeight: '40px', borderRadius: '20px',
            background: TK.bg, padding: '0 14px', fontSize: '13px',
            color: commentText.trim() ? TK.ink : TK.ink4, outline: 'none',
            border: `1px solid ${TK.dividerSoft}`, overflow: 'hidden',
            textOverflow: 'ellipsis', whiteSpace: 'nowrap' }">
          {{ commentText.trim() || t('task.addComment') }}
        </div>
        <button @click="statusSheet = true"
          :style="{ height: '40px', padding: '0 14px', borderRadius: '20px', background: TK.ink,
            color: '#fff', border: 'none', display: 'flex', alignItems: 'center', gap: '6px',
            fontSize: '13px', fontWeight: 600 }">
          <span :style="{ width: '6px', height: '6px', borderRadius: '3px',
            background: stat(d.status).color }" />
          {{ d.status_label }} <span :style="{ fontSize: '10px', opacity: 0.7 }">›</span>
        </button>
      </template>
    </div>

    <!-- Quick status sheet -->
    <Teleport to="body">
      <div v-if="statusSheet" :style="ovl" @click.self="statusSheet = false">
        <div :style="sheet">
          <div :style="grab" />
          <div :style="{ padding: '0 4px 4px' }">
            <div :style="{ fontSize: '11px', color: TK.ink3, letterSpacing: '0.6px',
              fontWeight: 600, textTransform: 'uppercase' }">{{ t('task.changeStatus') }}</div>
            <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '18px', fontWeight: 600, marginTop: '4px' }">
              {{ t('task.currently') }} · <span :style="{ color: stat(d.status).color }">{{ d.status_label }}</span>
            </div>
          </div>
          <div :style="{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }">
            <div v-for="op in statusOptions" :key="op.to" @click="doStatus(op)"
              :style="{ padding: '14px', background: TK.card, borderRadius: '12px',
                border: op.primary ? `1.5px solid ${TK.green}` : `1px solid ${TK.divider}`,
                display: 'flex', alignItems: 'center', gap: '14px',
                boxShadow: op.primary ? `0 0 0 3px ${TK.greenSoft}` : 'none' }">
              <div :style="{ width: '32px', height: '32px', borderRadius: '10px',
                background: op.primary ? op.tone : TK.bg, color: op.primary ? '#fff' : op.tone,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px' }">{{ op.icon }}</div>
              <div :style="{ flex: 1 }">
                <div :style="{ fontSize: '14px', fontWeight: 600, color: op.tone }">{{ op.l }}</div>
                <div v-if="op.sub" :style="{ fontSize: '11px', color: TK.ink3, marginTop: '2px' }">{{ op.sub }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Review approve/reject sheet -->
    <Teleport to="body">
      <div v-if="reviewSheet && !reviewCommentEditorOpen" :style="ovl" @click.self="reviewSheet = false">
        <div :style="sheet">
          <div :style="grab" />
          <div :style="{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.6px',
            textTransform: 'uppercase', color: reviewAction === 'approve' ? TK.green : TK.red }">
            {{ reviewAction === 'approve' ? t('task.approve') : t('task.reject') }}
          </div>
          <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '22px', fontWeight: 600, marginTop: '4px' }">
            {{ reviewAction === 'approve' ? t('task.approveTitle') : t('task.rejectTitle') }}
          </div>
          <div @click="reviewCommentEditorOpen = true"
            :style="{ marginTop: '14px', padding: '12px 14px', background: TK.card,
              borderRadius: '10px', border: `1px solid ${TK.divider}` }">
            <div :style="{ fontSize: '11px', color: TK.ink3, marginBottom: '6px',
              textTransform: 'uppercase', letterSpacing: '0.4px' }">
              {{ t('task.note') }}<span v-if="reviewAction === 'reject'" :style="{ color: TK.red }"> *</span>
            </div>
            <div :style="{ width: '100%', minHeight: '54px', fontSize: '13px',
              color: reviewComment.trim() ? TK.ink : TK.ink4, lineHeight: 1.55,
              whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: TK.sans }">
              {{ reviewComment.trim() || (reviewAction === 'reject' ? t('task.notePhReject') : t('task.notePhApprove')) }}
            </div>
          </div>
          <div :style="{ display: 'flex', gap: '10px', marginTop: '18px' }">
            <button @click="reviewSheet = false" :style="{ flex: 1, height: '46px',
              borderRadius: '23px', background: TK.card, border: `1.5px solid ${TK.divider}`,
              color: TK.ink2, fontSize: '14px', fontWeight: 600 }">{{ t('common.cancel') }}</button>
            <button @click="doReview" :style="{ flex: 2, height: '46px', borderRadius: '23px',
              background: reviewAction === 'approve' ? TK.green : TK.red, color: '#fff',
              border: 'none', fontSize: '14px', fontWeight: 600 }">
              {{ reviewAction === 'approve' ? t('task.confirmApprove') : t('task.confirmReject') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Subtask drawer (#5) -->
    <Teleport to="body">
      <div v-if="subSheet && curSub && !subTextEditorOpen" :style="ovl" @click.self="subSheet = false">
        <div :style="sheet">
          <div :style="grab" />
          <div :style="{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }">
            <span :style="{ fontSize: '11px', color: TK.ink3, letterSpacing: '0.6px',
              fontWeight: 600, textTransform: 'uppercase' }">{{ t('task.subDetail') }}</span>
            <span v-if="curSub.is_milestone" :style="{ fontSize: '9.5px', color: TK.purple,
              background: TK.purpleSoft, padding: '1px 6px', borderRadius: '3px',
              fontWeight: 700, textTransform: 'uppercase' }">{{ t('task.milestone') }}</span>
            <span :style="{ marginLeft: 'auto', ...chip(stat(curSub.status), 'md') }">{{ curSub.status_label }}</span>
          </div>
          <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '20px', fontWeight: 600,
            marginTop: '6px', lineHeight: 1.3 }">{{ curSub.title }}</div>
          <div :style="{ fontSize: '12px', color: TK.ink3, marginTop: '6px' }">
            {{ curSub.owner_name || '—' }} · {{ curSub.start || '—' }} – {{ curSub.due || '—' }}
          </div>

          <!-- progress notes -->
          <div :style="{ marginTop: '16px', fontSize: '11px', color: TK.ink3,
            fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }">
            {{ t('task.tlUpdate') }}</div>
          <div :style="{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '8px',
            maxHeight: '34vh', overflowY: 'auto' }">
            <div v-for="(r, i) in subProgress" :key="i"
              :style="{ background: TK.blueSoft, borderRadius: '8px', padding: '8px 12px',
                border: '1px solid #DCE6F2' }">
              <div :style="{ fontSize: '12.5px', color: TK.ink, lineHeight: 1.5 }">{{ r.text }}</div>
              <div :style="{ fontSize: '10px', color: TK.ink3, marginTop: '4px' }">{{ r.author }} · {{ r.at }}</div>
            </div>
            <div v-if="!subProgress.length" :style="{ fontSize: '12px', color: TK.ink4,
              padding: '8px 0' }">{{ t('task.subNoProgress') }}</div>
          </div>

          <!-- add progress -->
          <div :style="{ marginTop: '14px' }">
            <div @click="subTextEditorOpen = true"
              :style="{ width: '100%', boxSizing: 'border-box', height: '40px',
                lineHeight: '40px', borderRadius: '20px', background: TK.card,
                padding: '0 14px', fontSize: '13px',
                color: subText.trim() ? TK.ink : TK.ink4, outline: 'none',
                border: `1px solid ${TK.divider}`, overflow: 'hidden',
                textOverflow: 'ellipsis', whiteSpace: 'nowrap' }">
              {{ subText.trim() || t('task.subProgressPh') }}
            </div>
          </div>

          <!-- milestone confirm (I'm a pending confirmer) -->
          <div v-if="curSub.can_confirm_milestone"
            :style="{ display: 'flex', gap: '10px', marginTop: '16px' }">
            <button @click="openMs('reject')"
              :style="{ flex: 1, height: '46px', borderRadius: '23px', background: TK.card,
                color: TK.red, border: `1.5px solid ${TK.red}`, fontSize: '14px', fontWeight: 600 }">
              {{ t('task.msReject') }}</button>
            <button @click="openMs('confirm')"
              :style="{ flex: 2, height: '46px', borderRadius: '23px', background: TK.purple,
                color: '#fff', border: 'none', fontSize: '14px', fontWeight: 600 }">
              {{ t('task.msConfirm') }}</button>
          </div>

          <!-- status actions -->
          <div :style="{ display: 'flex', gap: '10px',
            marginTop: curSub.can_confirm_milestone ? '10px' : '16px' }">
            <button v-if="curSub.status === 'pending'" @click="doSubStatus('start')"
              :style="{ flex: 1, height: '46px', borderRadius: '23px', background: TK.card,
                border: `1.5px solid ${TK.divider}`, color: TK.ink2, fontSize: '14px',
                fontWeight: 600 }">{{ t('task.subStart') }}</button>
            <button v-if="curSub.status !== 'completed'" @click="doSubStatus('complete')"
              :style="{ flex: 2, height: '46px', borderRadius: '23px', background: TK.green,
                color: '#fff', border: 'none', fontSize: '14px', fontWeight: 600 }">
              {{ t('task.stComplete') }}</button>
            <button v-else @click="subSheet = false"
              :style="{ flex: 1, height: '46px', borderRadius: '23px', background: TK.card,
                border: `1.5px solid ${TK.divider}`, color: TK.ink2, fontSize: '14px',
                fontWeight: 600 }">{{ t('common.cancel') }}</button>
          </div>

          <!-- edit / delete subtask -->
          <div v-if="d.can_subtask" :style="{ display: 'flex', gap: '10px', marginTop: '10px' }">
            <button @click="openSubForm(curSub)"
              :style="{ flex: 1, height: '42px', borderRadius: '21px', background: TK.card,
                border: `1px solid ${TK.divider}`, color: TK.ink2, fontSize: '13px',
                fontWeight: 600 }">{{ t('common.edit') }}</button>
            <button @click="delSub(curSub)"
              :style="{ flex: 1, height: '42px', borderRadius: '21px', background: TK.card,
                border: `1px solid ${TK.redSoft}`, color: TK.red, fontSize: '13px',
                fontWeight: 600 }">{{ t('common.delete') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Subtask create/edit form sheet -->
    <Teleport to="body">
      <div v-if="subFormSheet" :style="ovl" @click.self="subFormSheet = false">
        <div :style="sheet">
          <div :style="grab" />
          <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '18px',
            fontWeight: 600, marginBottom: '12px' }">
            {{ subFormMode === 'edit' ? t('task.subFormEdit') : t('task.subFormNew') }}</div>

          <input v-model="sf.title" :placeholder="t('task.fTitlePh')"
            :style="{ width: '100%', boxSizing: 'border-box', padding: '12px 14px',
              background: TK.card, border: `1px solid ${TK.divider}`, borderRadius: '10px',
              fontSize: '15px', color: TK.ink, outline: 'none', marginBottom: '10px' }" />

          <div @click="sfAssigneeSheet = true"
            :style="{ display: 'flex', alignItems: 'center', padding: '11px 14px',
              background: TK.card, border: `1px solid ${TK.divider}`, borderRadius: '10px',
              marginBottom: '10px' }">
            <span :style="{ fontSize: '13px', color: sfAssigneeName ? TK.ink : TK.ink4 }">
              {{ sfAssigneeName || t('task.fAssigneePh') }}</span>
            <span :style="{ marginLeft: 'auto', color: TK.ink4 }">›</span>
          </div>

          <div :style="{ display: 'flex', gap: '10px', marginBottom: '10px' }">
            <input type="date" v-model="sf.start_date"
              :style="{ flex: 1, padding: '10px 12px', background: TK.card,
                border: `1px solid ${TK.divider}`, borderRadius: '10px', fontSize: '13px',
                color: TK.ink, outline: 'none' }" />
            <input type="date" v-model="sf.due_date"
              :style="{ flex: 1, padding: '10px 12px', background: TK.card,
                border: `1px solid ${TK.divider}`, borderRadius: '10px', fontSize: '13px',
                color: TK.ink, outline: 'none' }" />
          </div>

          <div @click="sf.is_milestone = !sf.is_milestone"
            :style="{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 0' }">
            <span :style="{ width: '18px', height: '18px', borderRadius: '5px',
              border: `1.5px solid ${sf.is_milestone ? TK.purple : TK.divider}`,
              background: sf.is_milestone ? TK.purple : 'transparent', color: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '12px' }">{{ sf.is_milestone ? '✓' : '' }}</span>
            <span :style="{ fontSize: '13.5px', color: TK.ink }">{{ t('task.subIsMilestone') }}</span>
          </div>

          <template v-if="sf.is_milestone">
            <textarea v-model="sf.milestone_criteria" rows="2"
              :placeholder="t('task.subMsCriteria')"
              :style="{ width: '100%', boxSizing: 'border-box', padding: '10px 14px',
                background: TK.card, border: `1px solid ${TK.divider}`, borderRadius: '10px',
                fontSize: '13px', color: TK.ink, outline: 'none', resize: 'none',
                margin: '6px 0 10px', fontFamily: TK.sans }" />
            <div @click="sfConfirmerSheet = true"
              :style="{ display: 'flex', alignItems: 'center', padding: '11px 14px',
                background: TK.card, border: `1px solid ${TK.divider}`, borderRadius: '10px',
                marginBottom: '10px' }">
              <span :style="{ fontSize: '13px', color: sfConfirmerNames ? TK.ink : TK.ink4 }">
                {{ sfConfirmerNames || t('task.subMsConfirmers') }}</span>
              <span :style="{ marginLeft: 'auto', color: TK.ink4 }">›</span>
            </div>
          </template>

          <div :style="{ display: 'flex', gap: '10px', marginTop: '8px' }">
            <button @click="subFormSheet = false"
              :style="{ flex: 1, height: '46px', borderRadius: '23px', background: TK.card,
                border: `1.5px solid ${TK.divider}`, color: TK.ink2, fontSize: '14px',
                fontWeight: 600 }">{{ t('common.cancel') }}</button>
            <button @click="saveSubForm" :style="{ flex: 2, height: '46px', borderRadius: '23px',
              background: sf.title.trim() ? TK.ink : TK.ink4, color: '#fff', border: 'none',
              fontSize: '14px', fontWeight: 600 }">{{ t('common.save') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Milestone confirm/reject sheet -->
    <Teleport to="body">
      <div v-if="msSheet && curSub && !msCommentEditorOpen" :style="ovl" @click.self="msSheet = false">
        <div :style="sheet">
          <div :style="grab" />
          <div :style="{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.6px',
            textTransform: 'uppercase', color: msAction === 'confirm' ? TK.purple : TK.red }">
            {{ msAction === 'confirm' ? t('task.msConfirm') : t('task.msReject') }}
          </div>
          <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '20px', fontWeight: 600,
            marginTop: '4px' }">
            {{ msAction === 'confirm' ? t('task.msConfirmTitle') : t('task.msRejectTitle') }}
          </div>
          <div @click="msCommentEditorOpen = true"
            :style="{ marginTop: '14px', padding: '12px 14px', background: TK.card,
              borderRadius: '10px', border: `1px solid ${TK.divider}` }">
            <div :style="{ fontSize: '11px', color: TK.ink3, marginBottom: '6px',
              textTransform: 'uppercase', letterSpacing: '0.4px' }">
              {{ t('task.note') }}<span v-if="msAction === 'reject'" :style="{ color: TK.red }"> *</span>
            </div>
            <div :style="{ width: '100%', minHeight: '54px', fontSize: '13px',
              color: msComment.trim() ? TK.ink : TK.ink4, lineHeight: 1.55,
              whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: TK.sans }">
              {{ msComment.trim() || (msAction === 'reject' ? t('task.msNoteReject') : t('task.msNotePh')) }}
            </div>
          </div>
          <div :style="{ display: 'flex', gap: '10px', marginTop: '18px' }">
            <button @click="msSheet = false" :style="{ flex: 1, height: '46px',
              borderRadius: '23px', background: TK.card, border: `1.5px solid ${TK.divider}`,
              color: TK.ink2, fontSize: '14px', fontWeight: 600 }">{{ t('common.cancel') }}</button>
            <button @click="doMs" :style="{ flex: 2, height: '46px', borderRadius: '23px',
              background: msAction === 'confirm' ? TK.purple : TK.red, color: '#fff',
              border: 'none', fontSize: '14px', fontWeight: 600 }">
              {{ msAction === 'confirm' ? t('task.msConfirm') : t('task.msReject') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <PersonPickerSheet v-model="sfAssigneeSheet" :title="t('task.fAssignee')" :options="people"
      :selected="sf.assignee_id" @update:selected="v => { sf.assignee_id = v }" />
    <MultiPersonPickerSheet v-model="sfConfirmerSheet" :title="t('task.subMsConfirmers')"
      :options="people" :selected="sf.milestone_confirmer_ids"
      @update:selected="v => { sf.milestone_confirmer_ids = v }" />

    <FullscreenTextEditor v-model="commentEditorOpen" :value="commentText"
      :title="t('task.addComment')" :placeholder="t('task.addComment')"
      :save-label="t('task.send')" @save="v => sendComment(v)" />
    <FullscreenTextEditor v-model="subTextEditorOpen" :value="subText"
      :title="t('task.tlUpdate')" :placeholder="t('task.subProgressPh')"
      :save-label="t('task.send')" @save="v => sendSubProgress(v)" />
    <FullscreenTextEditor v-model="reviewCommentEditorOpen" :value="reviewComment"
      :title="t('task.note')"
      :placeholder="reviewAction === 'reject' ? t('task.notePhReject') : t('task.notePhApprove')"
      @save="v => { reviewComment = v }" />
    <FullscreenTextEditor v-model="msCommentEditorOpen" :value="msComment"
      :title="t('task.note')"
      :placeholder="msAction === 'reject' ? t('task.msNoteReject') : t('task.msNotePh')"
      @save="v => { msComment = v }" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Browser } from '@capacitor/browser'
import { getTask, changeTaskStatus, addTaskReply, reviewTask,
  uploadTaskAttachment, deleteTaskAttachment, setSubtaskStatus,
  createSubtask, updateSubtask, deleteSubtask, confirmMilestone,
  resubmitReview, markTaskNotifsRead } from '@/api/tasks'
import { getAttributedCandidates } from '@/api/expense'
import client from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import PersonPickerSheet from '@/components/common/PersonPickerSheet.vue'
import MultiPersonPickerSheet from '@/components/common/MultiPersonPickerSheet.vue'
import FullscreenTextEditor from '@/components/common/FullscreenTextEditor.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const auth = useAuthStore()

const fileInput = ref(null)
const uploading = ref(false)
const _fileHost = (client.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '')

function extOf(name) {
  const m = (name || '').match(/\.([a-z0-9]{1,5})$/i)
  return (m?.[1] || 'FILE').toUpperCase().slice(0, 4)
}
function fmtSize(b) {
  if (!b) return ''
  if (b < 1024) return b + 'B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(0) + 'KB'
  return (b / 1024 / 1024).toFixed(1) + 'MB'
}
function openAtt(a) {
  if (!a.url) return
  const tok = localStorage.getItem('access_token') || ''
  const sep = a.url.includes('?') ? '&' : '?'
  Browser.open({ url: `${_fileHost}${a.url}${sep}token=${encodeURIComponent(tok)}` })
}
function pickFile() { if (!uploading.value) fileInput.value?.click() }
async function onFile(e) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', f)
    await uploadTaskAttachment(id.value, fd)
    await load()
  } catch (err) { /* noop */ } finally {
    uploading.value = false
  }
}
async function delAtt(a) {
  if (!window.confirm(t('task.delAttachment'))) return
  try {
    await deleteTaskAttachment(id.value, a.id)
    await load()
  } catch (err) { /* noop */ }
}

const subSheet = ref(false)
const curSub = ref(null)
const subText = ref('')
const subProgress = computed(() => {
  if (!curSub.value) return []
  return (d.value?.timeline || []).filter(r => r.sub && r.sub === curSub.value.title)
})
function openSub(s) { curSub.value = s; subText.value = ''; subSheet.value = true }
function _refreshSub() {
  if (!curSub.value) return
  const found = (d.value?.subtasks || []).find(x => x.id === curSub.value.id)
  if (found) curSub.value = found
  else subSheet.value = false
}
async function doSubStatus(action) {
  if (_busy.value) return
  _busy.value = true
  try {
    await setSubtaskStatus(id.value, curSub.value.id, action)
    await load()
    _refreshSub()
  } catch (e) { /* noop */ } finally { _busy.value = false }
}
async function sendSubProgress(text) {
  const c = (text ?? subText.value).trim()
  if (!c || _busy.value) return
  _busy.value = true
  subText.value = ''
  try {
    await addTaskReply(id.value, c, curSub.value.id)
    await load()
    _refreshSub()
  } catch (e) { subText.value = c } finally { _busy.value = false }
}

// ── subtask create/edit/delete + milestone confirm + resubmit ──
const _busy = ref(false)  // write-action re-entrancy guard (no dup create/submit)
const people = ref([])
const subFormSheet = ref(false)
const subFormMode = ref('new')
const sfAssigneeSheet = ref(false)
const sfConfirmerSheet = ref(false)
const sfEditId = ref(null)
const sf = reactive({ title: '', assignee_id: null, start_date: '', due_date: '',
  is_milestone: false, milestone_criteria: '', milestone_confirmer_ids: [] })
const sfAssigneeName = computed(() =>
  people.value.find(p => p.id === sf.assignee_id)?.name || '')
const sfConfirmerNames = computed(() => {
  const m = new Map(people.value.map(p => [p.id, p.name]))
  return (sf.milestone_confirmer_ids || []).map(i => m.get(i)).filter(Boolean).join('、')
})
function openSubForm(s) {
  if (s) {
    subFormMode.value = 'edit'
    sfEditId.value = s.id
    sf.title = s.title || ''
    sf.assignee_id = s.assignee_id || null
    sf.start_date = s.start_date ? String(s.start_date).slice(0, 10) : ''
    sf.due_date = s.due_date ? String(s.due_date).slice(0, 10) : ''
    sf.is_milestone = !!s.is_milestone
    sf.milestone_criteria = s.milestone_criteria || ''
    sf.milestone_confirmer_ids = (s.milestone_reviewers || []).map(r => r.reviewer_id)
  } else {
    subFormMode.value = 'new'
    sfEditId.value = null
    sf.title = ''; sf.assignee_id = null; sf.start_date = ''; sf.due_date = ''
    sf.is_milestone = false; sf.milestone_criteria = ''; sf.milestone_confirmer_ids = []
  }
  subFormSheet.value = true
}
async function saveSubForm() {
  if (!sf.title.trim() || _busy.value) return
  _busy.value = true
  const payload = {
    title: sf.title.trim(),
    assignee_id: sf.assignee_id || null,
    start_date: sf.start_date || null,
    due_date: sf.due_date || null,
    is_milestone: sf.is_milestone,
    milestone_criteria: sf.is_milestone ? (sf.milestone_criteria || '') : '',
    milestone_confirmer_ids: sf.is_milestone ? sf.milestone_confirmer_ids : [],
  }
  try {
    if (subFormMode.value === 'edit') {
      await updateSubtask(id.value, sfEditId.value, payload)
    } else {
      await createSubtask(id.value, payload)
    }
    subFormSheet.value = false
    await load()
    _refreshSub()
  } catch (e) { /* noop */ } finally { _busy.value = false }
}
async function delSub(s) {
  if (_busy.value || !window.confirm(t('task.subDelConfirm'))) return
  _busy.value = true
  try {
    await deleteSubtask(id.value, s.id)
    subSheet.value = false
    await load()
  } catch (e) { /* noop */ } finally { _busy.value = false }
}

const msSheet = ref(false)
const msAction = ref('confirm')
const msComment = ref('')
function openMs(a) { msAction.value = a; msComment.value = ''; msSheet.value = true }
async function doMs() {
  if (msAction.value === 'reject' && !msComment.value.trim()) return
  if (_busy.value) return
  _busy.value = true
  try {
    await confirmMilestone(id.value, curSub.value.id,
      { action: msAction.value, comment: msComment.value.trim() })
    msSheet.value = false
    await load()
    _refreshSub()
  } catch (e) { /* noop */ } finally { _busy.value = false }
}

async function doResubmit() {
  if (_busy.value) return
  _busy.value = true
  try {
    await resubmitReview(id.value)
    await load()
  } catch (e) { /* noop */ } finally { _busy.value = false }
}

const TK = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A',
  ink3: '#7A7570', ink4: '#B5AEA3', divider: '#EBE6DD', dividerSoft: '#F2EEE6',
  accent: '#D97757', accentSoft: '#FAEEE5', blue: '#3A6FB7', blueSoft: '#E5EBF4',
  green: '#2F7A4F', greenSoft: '#E9F1EB', warn: '#C77B22', warnSoft: '#F9F1E6',
  red: '#B5453A', redSoft: '#F4E4E1', purple: '#7B5BAC', purpleSoft: '#EEE6F5',
  sans: '-apple-system, "SF Pro Text", "PingFang SC", system-ui, sans-serif',
}
const STATUS_TK = {
  pending: { color: TK.ink3, bg: '#EFEAE2' }, in_progress: { color: TK.blue, bg: TK.blueSoft },
  paused: { color: TK.warn, bg: TK.warnSoft }, pending_review: { color: TK.purple, bg: TK.purpleSoft },
  completed: { color: TK.green, bg: TK.greenSoft }, cancelled: { color: TK.ink4, bg: '#EFEAE2' },
}
const PRIORITY_TK = {
  urgent: { color: TK.red, bg: TK.redSoft }, high: { color: TK.warn, bg: TK.warnSoft },
  normal: { color: TK.ink3, bg: '#EFEAE2' }, low: { color: TK.ink4, bg: '#F2EEE6' },
}
const _AVA = [TK.blue, TK.purple, TK.warn, TK.green, TK.red, TK.accent]
function stat(k) { return STATUS_TK[k] || STATUS_TK.pending }
function pri(k) { return PRIORITY_TK[k] || PRIORITY_TK.normal }
function chip(p, sz) {
  return { fontSize: sz === 'md' ? '11px' : '10px', color: p.color, background: p.bg,
    padding: sz === 'md' ? '3px 9px' : '2px 7px', borderRadius: '4px', fontWeight: 600,
    letterSpacing: '0.3px', whiteSpace: 'nowrap' }
}
function shortOf(name) {
  if (!name) return '?'
  const n = name.trim()
  if (/^[\x00-\x7F]/.test(n)) return n.split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase()
  return n.slice(-1)
}
function ava(name, size) {
  let h = 0; for (const c of (name || '?')) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return { width: size + 'px', height: size + 'px', borderRadius: (size / 2) + 'px',
    background: _AVA[h % _AVA.length], color: '#fff', display: 'inline-flex',
    alignItems: 'center', justifyContent: 'center', fontSize: (size * 0.4) + 'px',
    fontWeight: 700, flexShrink: 0 }
}
const secTitle = { padding: '20px 20px 10px', fontSize: '11px', color: TK.ink3,
  letterSpacing: '0.6px', fontWeight: 600, textTransform: 'uppercase' }
const ovl = { position: 'fixed', inset: 0, background: 'rgba(26,26,26,.42)', zIndex: 60 }
const sheet = { position: 'absolute', left: 0, right: 0, bottom: 0, background: TK.bg,
  borderRadius: '20px 20px 0 0', padding: '14px 16px calc(26px + env(safe-area-inset-bottom))',
  boxShadow: '0 -10px 30px rgba(0,0,0,.18)', maxHeight: '86%', overflowY: 'auto' }
const grab = { width: '36px', height: '4px', background: TK.divider, borderRadius: '2px', margin: '0 auto 14px' }

const id = computed(() => route.params.id)
const d = ref(null)
const loading = ref(true)
const commentText = ref('')
const commentEditorOpen = ref(false)
const subTextEditorOpen = ref(false)
const reviewCommentEditorOpen = ref(false)
const msCommentEditorOpen = ref(false)
const statusSheet = ref(false)
const reviewSheet = ref(false)
const reviewAction = ref('approve')
const reviewComment = ref('')

const taskCode = computed(() => 'T-' + String(d.value?.id || '').padStart(4, '0'))
function fmt(iso) {
  if (!iso) return '—'
  const dt = new Date(iso)
  return `${dt.getMonth() + 1}/${dt.getDate()} ${String(dt.getHours()).padStart(2, '0')}:${String(dt.getMinutes()).padStart(2, '0')}`
}
function fmtDate(iso) {
  if (!iso) return null
  const dt = new Date(iso)
  return `${dt.getMonth() + 1}/${dt.getDate()}`
}
const metaCells = computed(() => d.value ? [
  { l: t('task.mAssignee'), v: d.value.assignee_name },
  { l: t('task.mCreator'), v: d.value.creator_name },
  { l: t('task.mStart'), v: fmtDate(d.value.start_date) },
  { l: t('task.mDue'), v: fmtDate(d.value.due_date), accent: d.value.overdue },
] : [])
const sharedNames = computed(() => (d.value?.shared_names || []).join('、'))
const linkRows = computed(() => d.value ? [
  { l: t('task.lProject'), v: d.value.project_name },
  { l: t('task.lCustomer'), v: d.value.customer_name },
  { l: t('task.lQuotation'), v: d.value.quotation_number },
] : [])
const subDone = computed(() => (d.value?.subtasks || []).filter(s => s.status === 'completed').length)
const commentCount = computed(() => (d.value?.timeline || []).filter(r => r.kind !== 'system').length)

function rvTone(s) {
  if (s === 'approved') return { color: TK.green, bg: TK.greenSoft }
  if (s === 'rejected') return { color: TK.red, bg: TK.redSoft }
  return { color: TK.warn, bg: TK.warnSoft }
}
function rvLabel(s) {
  return s === 'approved' ? t('task.rvApproved') : s === 'rejected' ? t('task.rvRejected') : t('task.rvPending')
}

const statusOptions = computed(() => [
  { to: 'pending', icon: '◯', tone: TK.ink3, l: t('task.stBackTodo') },
  { to: 'paused', icon: '⏸', tone: TK.warn, l: t('task.stPause'), sub: t('task.stPauseSub'), needReason: true },
  { to: 'pending_review', icon: '↗', tone: TK.purple, l: t('task.stSubmitReview'), sub: t('task.stSubmitReviewSub') },
  { to: 'completed', icon: '✓', tone: TK.green, l: t('task.stComplete'), primary: true },
  { to: 'cancelled', icon: '✕', tone: TK.red, l: t('task.stCancel'), sub: t('task.stCancelSub') },
])

async function load() {
  loading.value = true
  try {
    const r = await getTask(id.value)
    d.value = r.data?.data || null
  } finally {
    loading.value = false
  }
}
async function sendComment(text) {
  const c = (text ?? commentText.value).trim()
  if (!c || _busy.value) return
  _busy.value = true
  commentText.value = ''
  try {
    const r = await addTaskReply(id.value, c)
    if (r.data?.data?.timeline) d.value.timeline = r.data.data.timeline
  } catch (e) { commentText.value = c } finally { _busy.value = false }
}
async function doStatus(op) {
  if (_busy.value) return
  let reason = ''
  if (op.needReason) {
    reason = (window.prompt(t('task.pausePrompt')) || '').trim()
    if (!reason) return
  }
  _busy.value = true
  try {
    await changeTaskStatus(id.value, { to: op.to, reason })
    statusSheet.value = false
    await load()
  } catch (e) { /* noop */ } finally { _busy.value = false }
}
function openReview(a) { reviewAction.value = a; reviewComment.value = ''; reviewSheet.value = true }
async function doReview() {
  if (reviewAction.value === 'reject' && !reviewComment.value.trim()) return
  if (_busy.value) return
  _busy.value = true
  try {
    await reviewTask(id.value, { action: reviewAction.value, comment: reviewComment.value.trim() })
    reviewSheet.value = false
    await load()
  } catch (e) { /* noop */ } finally { _busy.value = false }
}

onMounted(async () => {
  await load()
  markTaskNotifsRead(id.value).catch(() => {})  // opening task clears its unread
  try {
    const r = await getAttributedCandidates()
    people.value = (r.data?.data || []).map(u => ({
      id: u.id,
      name: u.name || u.real_name || u.username,
      department: u.department || u.dept || '',
    }))
  } catch (e) { /* noop */ }
})
</script>
