/**
 * Servetus — Claude App Conversation Exporter
 * ============================================
 * Paste this entire script into the DevTools console of the Claude desktop app
 * (or claude.ai in a browser) while the conversation you want is open.
 *
 * How to open DevTools in the Claude app:
 *   macOS: Cmd+Option+I  (or View → Developer → Developer Tools if available)
 *   Then click "Console" tab, paste this script, press Enter.
 *
 * What it does:
 *   1. Reads conversation data from the app's IndexedDB cache
 *   2. Falls back to scraping the visible DOM if IndexedDB is empty
 *   3. Formats as a Servetus artifact (YAML frontmatter + transcript)
 *   4. Triggers a .md file download
 *   5. Logs image URLs/UUIDs for manual download
 *
 * Output lands in: Inbox/Claude/ (move there manually after download)
 */

(async function servetusExport() {

  // ── 1. Try IndexedDB first ──────────────────────────────────────────────────

  async function readIndexedDB() {
    return new Promise((resolve) => {
      const req = indexedDB.open('claude-ai');
      req.onerror = () => resolve(null);
      req.onsuccess = (e) => {
        const db = e.target.result;
        const storeNames = Array.from(db.objectStoreNames);
        console.log('[Servetus] IndexedDB stores:', storeNames);

        // Try to find the conversations store
        const convStore = storeNames.find(s =>
          s.includes('conversation') || s.includes('messages') || s.includes('chat')
        );
        if (!convStore) { resolve(null); return; }

        const tx = db.transaction(convStore, 'readonly');
        const store = tx.objectStore(convStore);
        const all = store.getAll();
        all.onsuccess = () => resolve({ store: convStore, records: all.result });
        all.onerror = () => resolve(null);
      };
    });
  }

  // ── 2. Try the keyval-store (app state cache) ───────────────────────────────

  async function readKeyvalStore() {
    return new Promise((resolve) => {
      // The Claude app uses a db named after the origin
      const dbNames = ['claude-ai', 'keyval-store', 'localforage'];
      let tried = 0;
      const results = [];

      function tryNext(name) {
        const req = indexedDB.open(name);
        req.onerror = () => { tried++; if (tried === dbNames.length) resolve(results); };
        req.onsuccess = (e) => {
          const db = e.target.result;
          const storeNames = Array.from(db.objectStoreNames);
          let storeTried = 0;
          if (storeNames.length === 0) { tried++; if (tried === dbNames.length) resolve(results); return; }
          storeNames.forEach(storeName => {
            const tx = db.transaction(storeName, 'readonly');
            const store = tx.objectStore(storeName);
            const all = store.getAll();
            all.onsuccess = () => {
              if (all.result && all.result.length > 0) {
                results.push({ db: name, store: storeName, records: all.result });
              }
              storeTried++;
              if (storeTried === storeNames.length) {
                tried++;
                if (tried === dbNames.length) resolve(results);
              }
            };
            all.onerror = () => {
              storeTried++;
              if (storeTried === storeNames.length) {
                tried++;
                if (tried === dbNames.length) resolve(results);
              }
            };
          });
        };
      }

      dbNames.forEach(tryNext);
    });
  }

  // ── 3. DOM scraper fallback ─────────────────────────────────────────────────

  function scrapeDOM() {
    const messages = [];
    const images = [];

    // Claude app DOM selectors (as of early 2026 — may need updating)
    const selectors = [
      // Human messages
      { sel: '[data-testid="human-turn"]', role: 'human' },
      { sel: '.human-turn', role: 'human' },
      { sel: '[class*="HumanMessage"]', role: 'human' },
      // Assistant messages
      { sel: '[data-testid="ai-turn"]', role: 'assistant' },
      { sel: '.ai-turn', role: 'assistant' },
      { sel: '[class*="AssistantMessage"]', role: 'assistant' },
    ];

    // Try to find a conversation container
    const conversationContainer =
      document.querySelector('[data-testid="conversation"]') ||
      document.querySelector('[class*="conversation"]') ||
      document.querySelector('main') ||
      document.body;

    // Interleaved approach: walk the DOM tree and pick up all turns in order
    const allTurnEls = conversationContainer.querySelectorAll(
      '[data-testid="human-turn"], [data-testid="ai-turn"], ' +
      '.human-turn, .ai-turn, ' +
      '[class*="HumanTurn"], [class*="AssistantTurn"], ' +
      '[class*="human-message"], [class*="assistant-message"]'
    );

    if (allTurnEls.length === 0) {
      // Last resort: grab any large text blocks
      console.warn('[Servetus] No turn elements found. Attempting generic text extraction.');
      const paras = document.querySelectorAll('p, [class*="prose"]');
      paras.forEach(p => {
        const text = p.innerText?.trim();
        if (text && text.length > 20) {
          messages.push({ role: 'unknown', content: text, timestamp: null });
        }
      });
    } else {
      allTurnEls.forEach(el => {
        const isHuman =
          el.dataset.testid === 'human-turn' ||
          el.className?.includes?.('human') ||
          el.className?.includes?.('Human');
        const role = isHuman ? 'human' : 'assistant';
        const text = el.innerText?.trim() || '';

        // Grab timestamps from data attributes or aria labels
        const ts =
          el.dataset.timestamp ||
          el.dataset.createdAt ||
          el.querySelector('[data-timestamp]')?.dataset.timestamp ||
          el.querySelector('time')?.dateTime ||
          null;

        // Grab images
        el.querySelectorAll('img').forEach(img => {
          if (img.src && !img.src.includes('avatar') && !img.src.includes('icon')) {
            images.push({ src: img.src, alt: img.alt || '', turn: messages.length });
          }
        });

        if (text) {
          messages.push({ role, content: text, timestamp: ts });
        }
      });
    }

    return { messages, images };
  }

  // ── 4. Extract conversation from IndexedDB records ──────────────────────────

  function extractConversationFromRecords(records) {
    // Look for objects that look like conversation messages
    const messages = [];
    const images = [];

    function walk(obj, depth = 0) {
      if (!obj || depth > 5) return;
      if (Array.isArray(obj)) { obj.forEach(item => walk(item, depth + 1)); return; }
      if (typeof obj !== 'object') return;

      // Check if this looks like a message
      const hasSender = obj.sender || obj.role || obj.type;
      const hasContent = obj.content || obj.text || obj.body;
      if (hasSender && hasContent) {
        const roleRaw = (obj.sender || obj.role || obj.type || '').toLowerCase();
        const role = roleRaw.includes('human') || roleRaw.includes('user') ? 'human' : 'assistant';
        let content = '';
        if (typeof hasContent === 'string') {
          content = hasContent;
        } else if (Array.isArray(hasContent)) {
          content = hasContent
            .filter(b => b.type === 'text')
            .map(b => b.text || '')
            .join('\n');
          // Also grab image blocks
          hasContent.filter(b => b.type === 'image' || b.type === 'file').forEach(b => {
            const src = b.url || b.path || b.file_uuid || '';
            if (src) images.push({ src, alt: b.name || '', turn: messages.length });
          });
        }
        if (content.trim()) {
          messages.push({
            role,
            content: content.trim(),
            timestamp: obj.created_at || obj.timestamp || obj.updatedAt || null,
          });
        }
      }

      Object.values(obj).forEach(v => walk(v, depth + 1));
    }

    records.forEach(r => walk(r));
    return { messages, images };
  }

  // ── 5. Build Servetus artifact markdown ─────────────────────────────────────

  function buildArtifact(messages, images, source) {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const dateStr = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
    const timeStr = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;

    // Get timestamps from messages if available
    const tsList = messages.map(m => m.timestamp).filter(Boolean);
    let openedStr = dateStr + 'T' + timeStr;
    let closedStr = openedStr;
    if (tsList.length > 0) {
      // Handle both ISO strings and epoch ms
      const toDate = (t) => {
        if (typeof t === 'number' || (typeof t === 'string' && /^\d{13}$/.test(t))) {
          return new Date(Number(t));
        }
        return new Date(t);
      };
      const dates = tsList.map(toDate).filter(d => !isNaN(d));
      if (dates.length > 0) {
        openedStr = dates[0].toISOString();
        closedStr = dates[dates.length - 1].toISOString();
      }
    }

    // Title from page
    const pageTitle = document.title?.replace(' - Claude', '').trim() || 'Claude Web Session';
    const slug = `${dateStr}-claude-web-${Date.now().toString(36)}`;

    const userTurns = messages.filter(m => m.role === 'human').length;
    const asstTurns = messages.filter(m => m.role === 'assistant').length;

    const formatTs = (tsRaw) => {
      if (!tsRaw) return '';
      const toDate = (t) => {
        if (typeof t === 'number' || (typeof t === 'string' && /^\d{13}$/.test(t))) {
          return new Date(Number(t));
        }
        return new Date(t);
      };
      const d = toDate(tsRaw);
      if (isNaN(d)) return String(tsRaw);
      return d.toISOString().replace('T', ' ').replace('Z', ' UTC');
    };

    const frontmatter = `---
type: artifact
title: "${pageTitle}"
slug: "${slug}"

date: ${openedStr}
closed: ${closedStr}
timezone: "America/Chicago"

origin:
  machine: "claude-web-app"
  source: "${source}"

source:
  type: claude-web
  turns: ${userTurns}

circles: []
published: false
tags: [artifact, session, claude-web]
---`;

    const lines = [`# ${pageTitle}\n`];
    lines.push(`**Source:** ${source}  `);
    lines.push(`**Exported:** ${now.toISOString()}  `);
    lines.push(`**Turns:** ${userTurns} user / ${asstTurns} assistant  `);

    if (images.length > 0) {
      lines.push(`**Images:** ${images.length} attached (see image log below)  `);
    }
    lines.push('\n---\n');
    lines.push('## Transcript\n');

    messages.forEach((msg) => {
      const label = msg.role === 'human' ? '**You**' : '**Claude**';
      const ts = formatTs(msg.timestamp);
      const tsSuffix = ts ? ` \`${ts}\`` : '';
      lines.push(`### ${label}${tsSuffix}\n`);
      lines.push(msg.content);
      lines.push('\n---\n');
    });

    if (images.length > 0) {
      lines.push('## Images\n');
      images.forEach((img, i) => {
        lines.push(`${i + 1}. \`${img.src}\`${img.alt ? ' — ' + img.alt : ''} (after turn ${img.turn})`);
      });
    }

    return frontmatter + '\n\n' + lines.join('\n');
  }

  // ── 6. Trigger download ─────────────────────────────────────────────────────

  function download(filename, content) {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    console.log(`[Servetus] Downloaded: ${filename}`);
  }

  // ── 7. Main ─────────────────────────────────────────────────────────────────

  console.log('[Servetus] Starting export...');

  let messages = [];
  let images = [];
  let source = 'dom-scrape';

  // Try IndexedDB
  try {
    const idbResult = await readIndexedDB();
    if (idbResult && idbResult.records && idbResult.records.length > 0) {
      console.log(`[Servetus] IndexedDB store "${idbResult.store}": ${idbResult.records.length} records`);
      const extracted = extractConversationFromRecords(idbResult.records);
      if (extracted.messages.length > 0) {
        messages = extracted.messages;
        images = extracted.images;
        source = `indexeddb:${idbResult.store}`;
        console.log(`[Servetus] Extracted ${messages.length} messages from IndexedDB`);
      }
    }
  } catch (err) {
    console.warn('[Servetus] IndexedDB read failed:', err.message);
  }

  // Try keyval stores
  if (messages.length === 0) {
    try {
      const kvResults = await readKeyvalStore();
      console.log('[Servetus] keyval stores found:', kvResults.map(r => `${r.db}/${r.store}(${r.records.length})`));
      for (const kv of kvResults) {
        const extracted = extractConversationFromRecords(kv.records);
        if (extracted.messages.length > messages.length) {
          messages = extracted.messages;
          images = extracted.images;
          source = `keyval:${kv.db}/${kv.store}`;
        }
      }
      if (messages.length > 0) {
        console.log(`[Servetus] Extracted ${messages.length} messages from keyval store`);
      }
    } catch (err) {
      console.warn('[Servetus] keyval read failed:', err.message);
    }
  }

  // Fall back to DOM
  if (messages.length === 0) {
    console.log('[Servetus] Falling back to DOM scrape...');
    const dom = scrapeDOM();
    messages = dom.messages;
    images = dom.images;
    source = 'dom-scrape';
    console.log(`[Servetus] DOM scraped: ${messages.length} messages, ${images.length} images`);
  }

  if (messages.length === 0) {
    console.error('[Servetus] No messages found. Make sure the conversation is open and fully loaded.');
    return;
  }

  // Build and download
  const content = buildArtifact(messages, images, source);
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const dateStr = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
  const filename = `${dateStr}-claude-web-${Date.now().toString(36)}.md`;

  download(filename, content);

  // Log image URLs for manual download
  if (images.length > 0) {
    console.log(`\n[Servetus] ${images.length} image(s) referenced:`);
    images.forEach((img, i) => {
      console.log(`  ${i+1}. ${img.src}`);
    });
    console.log('\nImages are hosted on claude.ai servers. Download them manually before the session expires.');
  }

  console.log(`[Servetus] Export complete: ${messages.length} messages`);

})();
