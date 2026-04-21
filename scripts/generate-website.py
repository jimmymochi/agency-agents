#!/usr/bin/env python3
"""
Generate a self-contained static website (docs/index.html)
from all agent markdown files in the repository.
Run from the repo root: python3 scripts/generate-website.py
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(REPO_ROOT, "docs")

CATEGORY_META = {
    "engineering":        {"label": "Engineering",        "emoji": "💻", "order": 1},
    "design":             {"label": "Design",             "emoji": "🎨", "order": 2},
    "marketing":          {"label": "Marketing",          "emoji": "📢", "order": 3},
    "sales":              {"label": "Sales",              "emoji": "💼", "order": 4},
    "product":            {"label": "Product",            "emoji": "📊", "order": 5},
    "paid-media":         {"label": "Paid Media",         "emoji": "💰", "order": 6},
    "strategy":           {"label": "Strategy",           "emoji": "♟️",  "order": 7},
    "project-management": {"label": "Project Management", "emoji": "📋", "order": 8},
    "support":            {"label": "Support",            "emoji": "🎧", "order": 9},
    "finance":            {"label": "Finance",            "emoji": "🏦", "order": 10},
    "testing":            {"label": "Testing",            "emoji": "🧪", "order": 11},
    "game-development":   {"label": "Game Development",   "emoji": "🎮", "order": 12},
    "academic":           {"label": "Academic",           "emoji": "🎓", "order": 13},
    "spatial-computing":  {"label": "Spatial Computing",  "emoji": "🥽", "order": 14},
    "integrations":       {"label": "Integrations",       "emoji": "🔗", "order": 15},
    "specialized":        {"label": "Specialized",        "emoji": "⭐", "order": 16},
}

COLOR_MAP = {
    "cyan":    "#06b6d4",
    "blue":    "#3b82f6",
    "green":   "#22c55e",
    "purple":  "#a855f7",
    "pink":    "#ec4899",
    "red":     "#ef4444",
    "orange":  "#f97316",
    "yellow":  "#eab308",
    "teal":    "#14b8a6",
    "indigo":  "#6366f1",
    "gray":    "#6b7280",
    "slate":   "#64748b",
    "violet":  "#8b5cf6",
    "emerald": "#10b981",
    "amber":   "#f59e0b",
    "lime":    "#84cc16",
    "sky":     "#0ea5e9",
    "rose":    "#f43f5e",
}


def parse_frontmatter(content):
    """Extract YAML frontmatter and body from markdown content."""
    fm = {}
    body = content
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            fm_text = content[3:end].strip()
            body = content[end + 4:].strip()
            for line in fm_text.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    fm[key.strip()] = val.strip()
    return fm, body


def collect_agents():
    """Walk all category directories and collect agent data."""
    categories = {}
    for cat_key, cat_info in CATEGORY_META.items():
        cat_dir = os.path.join(REPO_ROOT, cat_key)
        if not os.path.isdir(cat_dir):
            continue
        agents = []
        for fname in sorted(os.listdir(cat_dir)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(cat_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            fm, body = parse_frontmatter(content)
            name = fm.get("name", fname.replace(".md", "").replace("-", " ").title())
            agents.append({
                "id": f"{cat_key}/{fname}",
                "name": name,
                "emoji": fm.get("emoji", cat_info["emoji"]),
                "description": fm.get("description", ""),
                "vibe": fm.get("vibe", ""),
                "color": COLOR_MAP.get(fm.get("color", ""), "#6b7280"),
                "content": body,
            })
        if agents:
            categories[cat_key] = {
                **cat_info,
                "agents": agents,
            }
    return dict(sorted(categories.items(), key=lambda x: x[1]["order"]))


def generate_html(categories):
    # escape </script> to prevent HTML parser from ending the script block early
    data_json = json.dumps(categories, ensure_ascii=False, indent=None, separators=(",", ":"))
    data_json = data_json.replace("</", "<\\/")

    total_agents = sum(len(c["agents"]) for c in categories.values())
    total_cats = len(categories)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>The Agency — AI Specialists</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{
    --bg:#0f172a;--surface:#1e293b;--surface2:#334155;--border:#334155;
    --text:#f1f5f9;--text2:#94a3b8;--text3:#64748b;
    --accent:#6366f1;--accent2:#818cf8;
    --radius:10px;--sidebar-w:220px;--list-w:280px;
  }}
  html{{height:100%;scroll-behavior:smooth}}
  body{{
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    background:var(--bg);color:var(--text);height:100%;overflow:hidden;
    display:flex;flex-direction:column;
  }}
  /* ── Header ── */
  header{{
    display:flex;align-items:center;gap:12px;padding:0 20px;height:56px;
    background:var(--surface);border-bottom:1px solid var(--border);
    flex-shrink:0;
  }}
  header h1{{font-size:1.1rem;font-weight:700;color:var(--text)}}
  header .badge{{
    font-size:.7rem;padding:2px 8px;border-radius:99px;
    background:var(--accent);color:#fff;font-weight:600;
  }}
  .search-wrap{{margin-left:auto;position:relative}}
  .search-wrap input{{
    background:var(--surface2);border:1px solid var(--border);
    color:var(--text);border-radius:var(--radius);padding:6px 12px 6px 32px;
    font-size:.85rem;width:220px;outline:none;
    transition:border-color .2s;
  }}
  .search-wrap input:focus{{border-color:var(--accent)}}
  .search-wrap .icon{{
    position:absolute;left:10px;top:50%;transform:translateY(-50%);
    color:var(--text3);font-size:.9rem;pointer-events:none;
  }}
  /* ── Layout ── */
  .layout{{display:flex;flex:1;overflow:hidden}}
  /* ── Sidebar ── */
  aside{{
    width:var(--sidebar-w);background:var(--surface);
    border-right:1px solid var(--border);
    overflow-y:auto;flex-shrink:0;padding:8px 0;
  }}
  .cat-btn{{
    display:flex;align-items:center;gap:8px;width:100%;
    padding:9px 16px;background:none;border:none;cursor:pointer;
    color:var(--text2);font-size:.85rem;text-align:left;
    border-left:3px solid transparent;transition:all .15s;
  }}
  .cat-btn:hover{{background:var(--surface2);color:var(--text)}}
  .cat-btn.active{{
    background:rgba(99,102,241,.15);color:var(--accent2);
    border-left-color:var(--accent);font-weight:600;
  }}
  .cat-btn .count{{
    margin-left:auto;font-size:.7rem;color:var(--text3);
    background:var(--surface2);padding:1px 6px;border-radius:99px;
  }}
  .cat-btn.active .count{{background:rgba(99,102,241,.2);color:var(--accent2)}}
  /* ── Agent List ── */
  .agent-list{{
    width:var(--list-w);border-right:1px solid var(--border);
    overflow-y:auto;flex-shrink:0;background:var(--bg);
  }}
  .agent-list-header{{
    padding:12px 16px;border-bottom:1px solid var(--border);
    font-size:.8rem;font-weight:600;color:var(--text3);
    text-transform:uppercase;letter-spacing:.05em;
    position:sticky;top:0;background:var(--bg);z-index:1;
  }}
  .agent-item{{
    display:flex;align-items:flex-start;gap:10px;padding:12px 16px;
    cursor:pointer;border-bottom:1px solid rgba(255,255,255,.04);
    transition:background .15s;
  }}
  .agent-item:hover{{background:var(--surface)}}
  .agent-item.active{{background:rgba(99,102,241,.1);border-left:3px solid var(--accent)}}
  .agent-emoji{{
    font-size:1.3rem;width:32px;height:32px;display:flex;
    align-items:center;justify-content:center;flex-shrink:0;
    border-radius:8px;background:var(--surface2);
  }}
  .agent-info{{flex:1;min-width:0}}
  .agent-info .name{{font-size:.88rem;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .agent-info .desc{{font-size:.75rem;color:var(--text3);margin-top:3px;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
  /* ── Content ── */
  .content-area{{
    flex:1;overflow-y:auto;padding:32px 40px;min-width:0;
  }}
  .empty-state{{
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    height:100%;color:var(--text3);gap:12px;
  }}
  .empty-state .big{{font-size:3rem}}
  .empty-state h2{{font-size:1.2rem;color:var(--text2)}}
  .empty-state p{{font-size:.9rem;max-width:320px;text-align:center;line-height:1.5}}
  .stats{{display:flex;gap:24px;margin-bottom:32px;flex-wrap:wrap}}
  .stat{{background:var(--surface);border-radius:var(--radius);padding:16px 24px;flex:1;min-width:120px}}
  .stat .num{{font-size:1.8rem;font-weight:700;color:var(--accent2)}}
  .stat .lbl{{font-size:.8rem;color:var(--text3);margin-top:4px}}
  /* ── Markdown ── */
  .md{{max-width:860px;line-height:1.7}}
  .md h1{{font-size:1.6rem;font-weight:700;color:var(--text);margin-bottom:16px;
    padding-bottom:12px;border-bottom:1px solid var(--border)}}
  .md h2{{font-size:1.15rem;font-weight:700;color:var(--text);margin:24px 0 10px}}
  .md h3{{font-size:1rem;font-weight:600;color:var(--text2);margin:18px 0 8px}}
  .md p{{color:var(--text2);margin-bottom:12px;font-size:.93rem}}
  .md ul,.md ol{{color:var(--text2);margin:0 0 12px 20px;font-size:.93rem}}
  .md li{{margin-bottom:4px}}
  .md strong{{color:var(--text);font-weight:600}}
  .md code{{
    background:var(--surface2);color:#a5f3fc;
    padding:2px 6px;border-radius:4px;font-size:.82rem;font-family:monospace;
  }}
  .md pre{{
    background:var(--surface2);border-radius:var(--radius);
    padding:16px;overflow-x:auto;margin-bottom:16px;
    border:1px solid var(--border);
  }}
  .md pre code{{background:none;padding:0;color:#a5f3fc}}
  .md blockquote{{
    border-left:3px solid var(--accent);padding:8px 16px;
    margin:12px 0;background:rgba(99,102,241,.08);border-radius:0 var(--radius) var(--radius) 0;
  }}
  .md blockquote p{{margin:0}}
  .md a{{color:var(--accent2);text-decoration:none}}
  .md a:hover{{text-decoration:underline}}
  .md hr{{border:none;border-top:1px solid var(--border);margin:20px 0}}
  .md table{{width:100%;border-collapse:collapse;margin-bottom:16px;font-size:.88rem}}
  .md th{{background:var(--surface2);color:var(--text);padding:8px 12px;text-align:left;border:1px solid var(--border)}}
  .md td{{padding:8px 12px;border:1px solid var(--border);color:var(--text2)}}
  .md tr:nth-child(even) td{{background:rgba(255,255,255,.02)}}
  /* Agent header */
  .agent-header{{
    display:flex;align-items:center;gap:14px;margin-bottom:24px;
    padding:20px;background:var(--surface);border-radius:var(--radius);
    border:1px solid var(--border);
  }}
  .agent-header .big-emoji{{font-size:2.2rem}}
  .agent-header .agent-name{{font-size:1.4rem;font-weight:700;color:var(--text)}}
  .agent-header .agent-vibe{{font-size:.88rem;color:var(--text2);margin-top:4px;font-style:italic}}
  .color-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
  /* copy btn */
  .copy-btn{{
    display:inline-flex;align-items:center;gap:6px;
    margin-top:8px;padding:7px 14px;
    background:var(--accent);color:#fff;border:none;border-radius:var(--radius);
    font-size:.82rem;cursor:pointer;font-weight:600;transition:opacity .15s;
  }}
  .copy-btn:hover{{opacity:.85}}
  .copy-btn.copied{{background:#22c55e}}
  /* search highlight */
  mark{{background:rgba(99,102,241,.4);color:var(--text);border-radius:2px;padding:0 2px}}
  /* scrollbar */
  ::-webkit-scrollbar{{width:6px;height:6px}}
  ::-webkit-scrollbar-track{{background:transparent}}
  ::-webkit-scrollbar-thumb{{background:var(--surface2);border-radius:3px}}
  ::-webkit-scrollbar-thumb:hover{{background:var(--text3)}}
  /* responsive */
  @media(max-width:768px){{
    aside{{display:none}}
    .agent-list{{width:100%;max-width:100%;display:none}}
    .agent-list.mobile-show{{display:block}}
    .content-area{{padding:20px 16px}}
    :root{{--list-w:100vw}}
  }}
</style>
</head>
<body>

<header>
  <span style="font-size:1.5rem">🎭</span>
  <h1>The Agency</h1>
  <span class="badge">{total_agents} Agents</span>
  <div class="search-wrap">
    <span class="icon">🔍</span>
    <input type="text" id="search" placeholder="Search agents…" autocomplete="off"/>
  </div>
</header>

<div class="layout">
  <aside id="sidebar"></aside>
  <div class="agent-list" id="agentList"></div>
  <main class="content-area" id="content">
    <div class="empty-state">
      <div class="big">🎭</div>
      <h2>Welcome to The Agency</h2>
      <p>A curated collection of AI agent personalities. Select a category and agent to view their prompt.</p>
      <div class="stats">
        <div class="stat"><div class="num">{total_agents}</div><div class="lbl">Agents</div></div>
        <div class="stat"><div class="num">{total_cats}</div><div class="lbl">Categories</div></div>
      </div>
    </div>
  </main>
</div>

<script>
const DATA = {data_json};

let activeCat = null;
let activeAgent = null;
let searchQuery = "";

// ── Sidebar ──
const sidebar = document.getElementById("sidebar");
const agentListEl = document.getElementById("agentList");
const contentEl = document.getElementById("content");

function renderSidebar() {{
  sidebar.innerHTML = "";
  for (const [key, cat] of Object.entries(DATA)) {{
    const btn = document.createElement("button");
    btn.className = "cat-btn" + (activeCat === key ? " active" : "");
    btn.innerHTML = `<span>${{cat.emoji}}</span><span>${{cat.label}}</span><span class="count">${{cat.agents.length}}</span>`;
    btn.onclick = () => selectCategory(key);
    sidebar.appendChild(btn);
  }}
}}

function selectCategory(key) {{
  activeCat = key;
  activeAgent = null;
  renderSidebar();
  renderAgentList();
  showWelcome();
}}

// ── Agent List ──
function renderAgentList(filter) {{
  if (!activeCat && !filter) {{ agentListEl.innerHTML = ""; return; }}
  agentListEl.innerHTML = "";

  let agents = [];
  let headerLabel = "";

  if (filter) {{
    // search across all categories
    for (const [key, cat] of Object.entries(DATA)) {{
      for (const a of cat.agents) {{
        const q = filter.toLowerCase();
        if (a.name.toLowerCase().includes(q) || a.description.toLowerCase().includes(q)) {{
          agents.push({{...a, _cat: key, _catLabel: cat.label}});
        }}
      }}
    }}
    headerLabel = `${{agents.length}} result${{agents.length !== 1 ? "s" : ""}} for "${{filter}}"`;
  }} else {{
    agents = DATA[activeCat].agents;
    headerLabel = DATA[activeCat].label;
  }}

  const hdr = document.createElement("div");
  hdr.className = "agent-list-header";
  hdr.textContent = headerLabel;
  agentListEl.appendChild(hdr);

  for (const a of agents) {{
    const item = document.createElement("div");
    item.className = "agent-item" + (activeAgent && activeAgent.id === a.id ? " active" : "");
    item.innerHTML = `
      <div class="agent-emoji">${{a.emoji}}</div>
      <div class="agent-info">
        <div class="name">${{a.name}}</div>
        <div class="desc">${{a.description}}</div>
      </div>`;
    item.onclick = () => selectAgent(a);
    agentListEl.appendChild(item);
  }}
}}

// ── Agent Content ──
function selectAgent(agent) {{
  activeAgent = agent;
  renderSidebar();
  renderAgentList(searchQuery || null);
  // mark active
  agentListEl.querySelectorAll(".agent-item").forEach(el => {{
    el.classList.toggle("active", el.querySelector(".name").textContent === agent.name);
  }});
  showAgent(agent);
}}

function showAgent(agent) {{
  const rendered = marked.parse(agent.content || "");
  contentEl.innerHTML = `
    <div class="agent-header">
      <div class="big-emoji">${{agent.emoji}}</div>
      <div>
        <div class="agent-name">${{agent.name}}</div>
        ${{agent.vibe ? `<div class="agent-vibe">"${{agent.vibe}}"</div>` : ""}}
      </div>
      <div style="margin-left:auto;display:flex;flex-direction:column;align-items:flex-end;gap:8px">
        <div style="display:flex;align-items:center;gap:6px">
          <div class="color-dot" style="background:${{agent.color}}"></div>
          <span style="font-size:.75rem;color:var(--text3)">${{agent._catLabel || ""}}</span>
        </div>
        <button class="copy-btn" id="copyBtn">📋 Copy Prompt</button>
      </div>
    </div>
    <div class="md">${{rendered}}</div>`;

  document.getElementById("copyBtn").onclick = function() {{
    navigator.clipboard.writeText(agent.content).then(() => {{
      this.textContent = "✅ Copied!";
      this.classList.add("copied");
      setTimeout(() => {{ this.textContent = "📋 Copy Prompt"; this.classList.remove("copied"); }}, 2000);
    }});
  }};
  contentEl.scrollTop = 0;
}}

function showWelcome() {{
  const total = Object.values(DATA).reduce((s,c)=>s+c.agents.length,0);
  const cats = Object.keys(DATA).length;
  contentEl.innerHTML = `<div class="empty-state">
    <div class="big">🎭</div>
    <h2>The Agency</h2>
    <p>Select an agent from the list to view their full prompt and personality.</p>
    <div class="stats">
      <div class="stat"><div class="num">${{total}}</div><div class="lbl">Agents</div></div>
      <div class="stat"><div class="num">${{cats}}</div><div class="lbl">Categories</div></div>
    </div>
  </div>`;
}}

// ── Search ──
document.getElementById("search").addEventListener("input", function() {{
  searchQuery = this.value.trim();
  if (searchQuery) {{
    activeCat = null;
    renderSidebar();
    renderAgentList(searchQuery);
  }} else {{
    renderSidebar();
    renderAgentList();
  }}
}});

// ── Init ──
renderSidebar();
</script>
</body>
</html>"""


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    print("Collecting agents…")
    categories = collect_agents()
    total = sum(len(c["agents"]) for c in categories.values())
    print(f"Found {total} agents across {len(categories)} categories")

    html = generate_html(categories)
    out_path = os.path.join(DOCS_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated: {out_path} ({len(html)//1024} KB)")

    nojekyll = os.path.join(DOCS_DIR, ".nojekyll")
    if not os.path.exists(nojekyll):
        open(nojekyll, "w").close()
        print("Created: docs/.nojekyll")


if __name__ == "__main__":
    main()
