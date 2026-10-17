/**
 * Response Transparency Panel Component (M3.4)
 * Renders expandable evidence details, confidence badges, source attribution,
 * page/section numbers, chunk IDs, and similarity scores using verified metadata.
 */

class TransparencyPanel {
  /**
   * Renders the transparency panel HTML structure.
   * @param {Object} transparencyData - Contains confidence_score, confidence_label, sources, insufficient_evidence.
   * @returns {string} HTML string
   */
  static render(transparencyData) {
    if (!transparencyData) return '';

    const score = transparencyData.confidence_score || 0.0;
    const scorePct = Math.round(score * 100);
    const label = transparencyData.confidence_label || (score >= 0.60 ? 'High' : score >= 0.30 ? 'Medium' : 'Low');
    const badgeClass = label.toLowerCase();

    const sources = transparencyData.sources || [];
    const isInsufficient = transparencyData.insufficient_evidence || sources.length === 0;

    if (isInsufficient) {
      return `
        <div class="transparency-panel insufficient">
          <div class="transparency-header">
            <div class="confidence-badge low">
              <span class="confidence-dot"></span>
              <span>Confidence: Low (${score.toFixed(2)})</span>
            </div>
            <span class="evidence-count">0 Chunks Retrieved</span>
          </div>
          <div class="transparency-notice">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span>Insufficient supporting evidence was found in the knowledge base.</span>
          </div>
        </div>
      `;
    }

    const sourceCardsHtml = sources.map((src, idx) => {
      const docName = TransparencyPanel.escapeHtml(src.document_name || src.source_file || 'Document');
      const page = src.page || 1;
      const section = TransparencyPanel.escapeHtml(src.section || 'General');
      const chunkId = TransparencyPanel.escapeHtml(src.chunk_id || `chunk_${idx + 1}`);
      const relScore = (src.relevance_score || src.similarity_score || 0.0).toFixed(2);
      const excerpt = TransparencyPanel.escapeHtml(src.content || src.excerpt || '');

      return `
        <div class="transparency-chunk-card">
          <div class="chunk-meta-header">
            <div class="doc-title-row">
              <span class="file-icon">📄</span>
              <strong class="doc-name" title="${docName}">${docName}</strong>
            </div>
            <span class="relevance-tag">Relevance: ${relScore}</span>
          </div>
          
          <div class="chunk-details-grid">
            <span class="chunk-detail-pill"><strong>Page/Sec:</strong> ${section} (p. ${page})</span>
            <span class="chunk-detail-pill"><strong>Chunk ID:</strong> <code>${chunkId}</code></span>
          </div>

          <div class="chunk-evidence-quote">
            <p>"${excerpt}"</p>
          </div>
        </div>
      `;
    }).join('');

    return `
      <div class="transparency-panel">
        <div class="transparency-header">
          <div class="confidence-badge ${badgeClass}">
            <span class="confidence-dot"></span>
            <span>Confidence: ${label} (${score.toFixed(2)})</span>
          </div>
          
          <button class="transparency-toggle-btn" aria-expanded="false">
            <span>Sources & Evidence (${sources.length})</span>
            <svg class="chevron-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
        </div>

        <div class="transparency-content hidden">
          <div class="sources-grid">
            ${sourceCardsHtml}
          </div>
        </div>
      </div>
    `;
  }

  static attachListeners(panelContainer) {
    if (!panelContainer) return;
    const toggleBtn = panelContainer.querySelector('.transparency-toggle-btn');
    const content = panelContainer.querySelector('.transparency-content');

    if (toggleBtn && content) {
      toggleBtn.addEventListener('click', () => {
        const isHidden = content.classList.contains('hidden');
        if (isHidden) {
          content.classList.remove('hidden');
          toggleBtn.classList.add('open');
          toggleBtn.setAttribute('aria-expanded', 'true');
        } else {
          content.classList.add('hidden');
          toggleBtn.classList.remove('open');
          toggleBtn.setAttribute('aria-expanded', 'false');
        }
      });
    }
  }

  static escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TransparencyPanel };
}
