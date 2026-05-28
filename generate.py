import requests, os, sys, base64

user = os.environ.get("GITHUB_USER", "emersonaparecidosilva")

headers = {
    "User-Agent": "portfolio-generator",
    "Accept": "application/vnd.github+json",
}

res = requests.get(
    f"https://api.github.com/users/{user}/repos?per_page=100&sort=updated",
    headers=headers
)

data = res.json()

if not isinstance(data, list):
    print(f"❌ Erro da API do GitHub: {data}")
    sys.exit(1)

repos = [r for r in data if not r["fork"] and r["name"] != f"{user}.github.io"]

langs = sorted(set(r.get("language") or "Outro" for r in repos))
n_langs = len(langs)

lang_colors = {
    "Python": "#4d9cf0",
    "Jupyter Notebook": "#f0a04d",
    "JavaScript": "#f0e04d",
    "TypeScript": "#5d9cf0",
    "HTML": "#f07a4d",
}

def card_color(lang):
    return lang_colors.get(lang, "#6a9a6a")

def fetch_readme(repo_name):
    url = f"https://api.github.com/repos/{user}/{repo_name}/readme"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json().get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="replace")
    return None

filter_buttons = ''.join(
    f'<button class="filter-btn" data-lang="{l}" onclick="filterCards(this)">{l}</button>'
    for l in langs
)

cards = ""
readmes_js = {}

for r in repos:
    lang = r.get("language") or "Outro"
    desc = r.get("description") or "Sem descrição"
    color = card_color(lang)
    topics = r.get("topics") or []
    pills = "".join(f'<span class="pill">{t}</span>' for t in topics[:2])
    if not pills:
        pills = f'<span class="pill">{lang}</span>'
    updated = r.get("pushed_at", "")[:10]
    name = r["name"]

    readme = fetch_readme(name)
    if readme:
        # Escapa para JSON seguro
        readme_escaped = readme.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        readmes_js[name] = readme_escaped
        detail_btn = f'<button class="detail-btn" onclick="showReadme(\'{name}\')">ver detalhes →</button>'
    else:
        detail_btn = f'<a class="detail-btn" href="{r["html_url"]}" target="_blank">ver no GitHub →</a>'

    cards += f"""
    <div class="card" data-lang="{lang}">
      <div class="card-top" style="background:{color}"></div>
      <div class="card-body">
        <div class="card-lang">{lang}</div>
        <h3><a href="{r['html_url']}" target="_blank">{name}</a></h3>
        <p>{desc}</p>
        <div class="card-footer">{pills}<span class="upd">{updated}</span></div>
        <div class="card-actions">{detail_btn}</div>
      </div>
    </div>"""

# Monta o JS com os READMEs
readmes_json_entries = ",\n".join(
    f'  "{k}": `{v}`' for k, v in readmes_js.items()
)

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Portfólio | Emerson Silva</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
  <!-- Markdown renderer -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #070b11; --surface: #0d1320; --surface2: #111827;
      --border: #1c2a3a; --border2: #243447;
      --blue: #4d9cf0; --blue-dim: #0f2d4a;
      --text: #dce8f8; --muted: #4a6a8a; --faint: #1a2a3a;
    }}
    body {{ font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }}

    header {{ max-width: 900px; margin: 0 auto; padding: 3rem 2rem 2rem; display: flex; gap: 2rem; align-items: flex-start; }}
    .avatar-wrap {{ position: relative; flex-shrink: 0; }}
    .avatar-wrap img {{ width: 110px; height: 110px; border-radius: 50%; object-fit: cover;
      border: 2px solid var(--border2); box-shadow: 0 0 0 4px var(--surface), 0 0 0 5px var(--border); }}
    .av-ring {{ position: absolute; inset: -6px; border-radius: 50%;
      border: 1.5px solid #1a3a5c; pointer-events: none; }}
    .header-info {{ flex: 1; padding-top: .3rem; }}
    .badge {{ display: inline-flex; align-items: center; gap: 5px; background: var(--blue-dim);
      color: var(--blue); font-size: .7rem; border-radius: 20px; padding: 3px 10px; margin-bottom: .7rem;
      font-family: 'DM Mono', monospace; }}
    .badge::before {{ content: ''; width: 6px; height: 6px; border-radius: 50%;
      background: var(--blue); display: inline-block; }}
    header h1 {{ font-size: 1.9rem; color: #e8f2ff; font-weight: 600; letter-spacing: -.5px; margin-bottom: .25rem; }}
    .role {{ color: var(--muted); font-size: .9rem; margin-bottom: 1rem; }}
    .stats {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 1rem; }}
    .stat {{ background: var(--surface); border: 0.5px solid var(--border); border-radius: 8px; padding: .45rem .9rem; }}
    .stat-num {{ color: #e8f2ff; font-size: 1.2rem; font-weight: 600; display: block; font-family: 'DM Mono', monospace; }}
    .stat-label {{ color: var(--muted); font-size: .7rem; }}
    .links {{ display: flex; gap: 10px; }}
    .link-btn {{ display: inline-flex; align-items: center; gap: 5px; color: var(--blue);
      background: var(--blue-dim); border: 0.5px solid #1a3a5c; border-radius: 20px;
      padding: 5px 14px; font-size: .8rem; text-decoration: none; transition: .15s; }}
    .link-btn:hover {{ background: #173860; border-color: var(--blue); }}

    .section-header {{ max-width: 900px; margin: 0 auto; padding: 0 2rem .75rem;
      display: flex; align-items: center; gap: 1rem; }}
    .section-header h2 {{ font-size: .8rem; color: var(--muted); font-weight: 500;
      text-transform: uppercase; letter-spacing: .8px; white-space: nowrap; }}
    .section-line {{ flex: 1; height: 0.5px; background: var(--border); }}

    .filters {{ max-width: 900px; margin: 0 auto; padding: 0 2rem 1.25rem;
      display: flex; gap: 6px; flex-wrap: wrap; }}
    .filter-btn {{ background: transparent; border: 0.5px solid var(--border2); border-radius: 20px;
      padding: 4px 14px; font-size: .78rem; color: var(--muted); cursor: pointer;
      transition: .15s; font-family: 'DM Sans', sans-serif; }}
    .filter-btn:hover {{ color: var(--blue); border-color: #1a3a5c; }}
    .filter-btn.active {{ background: var(--blue-dim); color: var(--blue); border-color: var(--blue); }}

    main {{ max-width: 900px; margin: 0 auto; padding: 0 2rem 4rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }}
    .card {{ background: var(--surface); border: 0.5px solid var(--border); border-radius: 10px;
      overflow: hidden; transition: border-color .2s, transform .2s; display: flex; flex-direction: column; }}
    .card:hover {{ border-color: #2a4a6a; transform: translateY(-2px); }}
    .card-top {{ height: 2.5px; flex-shrink: 0; }}
    .card-body {{ padding: 1rem; display: flex; flex-direction: column; flex: 1; }}
    .card-lang {{ font-size: .65rem; color: var(--muted); text-transform: uppercase;
      letter-spacing: .6px; margin-bottom: .3rem; font-family: 'DM Mono', monospace; }}
    .card h3 {{ font-size: .9rem; margin-bottom: .35rem; }}
    .card h3 a {{ color: var(--text); text-decoration: none; }}
    .card h3 a:hover {{ color: var(--blue); }}
    .card p {{ font-size: .8rem; color: var(--muted); line-height: 1.5; margin-bottom: .8rem; flex: 1; }}
    .card-footer {{ display: flex; align-items: center; gap: 5px; margin-bottom: .6rem; }}
    .pill {{ background: var(--blue-dim); color: var(--blue); font-size: .68rem;
      padding: 2px 8px; border-radius: 8px; font-family: 'DM Mono', monospace; }}
    .upd {{ margin-left: auto; color: var(--faint); font-size: .65rem; font-family: 'DM Mono', monospace; }}
    .card-actions {{ border-top: 0.5px solid var(--border); padding-top: .6rem; margin-top: auto; }}
    .detail-btn {{ background: none; border: none; color: var(--blue); font-size: .78rem;
      cursor: pointer; font-family: 'DM Sans', sans-serif; padding: 0; transition: .15s;
      text-decoration: none; display: inline-block; }}
    .detail-btn:hover {{ color: #7db8f7; }}

    /* MODAL */
    .modal-overlay {{ position: fixed; inset: 0; background: rgba(0,0,0,.7); backdrop-filter: blur(4px);
      z-index: 100; display: none; align-items: center; justify-content: center; padding: 1.5rem; }}
    .modal-overlay.open {{ display: flex; }}
    .modal {{ background: var(--surface); border: 0.5px solid var(--border2); border-radius: 14px;
      width: 100%; max-width: 720px; max-height: 85vh; display: flex; flex-direction: column;
      overflow: hidden; animation: slideUp .2s ease; }}
    @keyframes slideUp {{ from {{ opacity:0; transform:translateY(20px) }} to {{ opacity:1; transform:translateY(0) }} }}
    .modal-header {{ display: flex; align-items: center; justify-content: space-between;
      padding: 1rem 1.25rem; border-bottom: 0.5px solid var(--border); flex-shrink: 0; }}
    .modal-title {{ font-size: 1rem; color: var(--text); font-weight: 500; }}
    .modal-actions {{ display: flex; align-items: center; gap: 10px; }}
    .modal-gh {{ color: var(--blue); font-size: .8rem; text-decoration: none; }}
    .modal-gh:hover {{ text-decoration: underline; }}
    .modal-close {{ background: var(--faint); border: none; color: var(--muted); width: 28px; height: 28px;
      border-radius: 50%; cursor: pointer; font-size: 1rem; display: flex; align-items: center;
      justify-content: center; transition: .15s; }}
    .modal-close:hover {{ background: var(--border2); color: var(--text); }}
    .modal-body {{ overflow-y: auto; padding: 1.5rem; flex: 1; }}

    /* Markdown styles */
    .md-content h1,.md-content h2,.md-content h3 {{ color: #e8f2ff; margin: 1.2rem 0 .5rem; font-weight: 500; }}
    .md-content h1 {{ font-size: 1.4rem; border-bottom: 0.5px solid var(--border); padding-bottom: .4rem; }}
    .md-content h2 {{ font-size: 1.1rem; }}
    .md-content h3 {{ font-size: .95rem; }}
    .md-content p {{ font-size: .88rem; color: #9ab4cc; line-height: 1.7; margin-bottom: .8rem; }}
    .md-content a {{ color: var(--blue); }}
    .md-content code {{ background: var(--faint); color: #79c0ff; font-family: 'DM Mono', monospace;
      font-size: .8rem; padding: 2px 5px; border-radius: 4px; }}
    .md-content pre {{ background: #060a0f; border: 0.5px solid var(--border); border-radius: 8px;
      padding: 1rem; overflow-x: auto; margin-bottom: 1rem; }}
    .md-content pre code {{ background: none; padding: 0; color: #a8c8e8; }}
    .md-content ul, .md-content ol {{ padding-left: 1.5rem; margin-bottom: .8rem; }}
    .md-content li {{ font-size: .88rem; color: #9ab4cc; line-height: 1.7; }}
    .md-content img {{ max-width: 100%; border-radius: 6px; margin: .5rem 0; }}
    .md-content blockquote {{ border-left: 3px solid var(--blue); padding-left: 1rem;
      color: var(--muted); font-style: italic; margin-bottom: .8rem; }}
    .md-content table {{ width: 100%; border-collapse: collapse; margin-bottom: 1rem; font-size: .85rem; }}
    .md-content th {{ background: var(--faint); color: var(--text); padding: .5rem .75rem;
      border: 0.5px solid var(--border); text-align: left; }}
    .md-content td {{ padding: .5rem .75rem; border: 0.5px solid var(--border); color: #9ab4cc; }}

    footer {{ text-align: center; padding: 1.5rem 2rem; color: var(--faint); font-size: .75rem;
      border-top: 0.5px solid var(--border); max-width: 900px; margin: 0 auto; }}
    .card.hidden {{ display: none; }}
  </style>
</head>
<body>

  <header>
    <div class="avatar-wrap">
      <img src="foto.jpg" alt="Emerson Silva">
      <div class="av-ring"></div>
    </div>
    <div class="header-info">
      <div class="badge">disponível para colaborações</div>
      <h1>Emerson Silva</h1>
      <p class="role">Data Analytics · Data Science · Power BI</p>
      <div class="stats">
        <div class="stat"><span class="stat-num">{len(repos)}</span><span class="stat-label">projetos</span></div>
        <div class="stat"><span class="stat-num">{n_langs}</span><span class="stat-label">linguagens</span></div>
      </div>
      <div class="links">
        <a class="link-btn" href="https://github.com/{user}" target="_blank">⌥ GitHub</a>
        <a class="link-btn" href="https://www.linkedin.com/in/emersonasilva/" target="_blank">in LinkedIn</a>
      </div>
    </div>
  </header>

  <div class="section-header">
    <h2>projetos</h2>
    <div class="section-line"></div>
  </div>

  <div class="filters">
    <button class="filter-btn active" onclick="filterCards(this)" data-lang="all">Todos</button>
    {filter_buttons}
  </div>

  <main>
    <div class="grid">{cards}</div>
  </main>

  <footer>
    atualizado automaticamente via github actions &nbsp;·&nbsp; {len(repos)} repositórios
  </footer>

  <!-- MODAL -->
  <div class="modal-overlay" id="modal" onclick="closeOnOverlay(event)">
    <div class="modal">
      <div class="modal-header">
        <span class="modal-title" id="modal-title"></span>
        <div class="modal-actions">
          <a class="modal-gh" id="modal-gh-link" href="#" target="_blank">ver no GitHub ↗</a>
          <button class="modal-close" onclick="closeModal()">✕</button>
        </div>
      </div>
      <div class="modal-body">
        <div class="md-content" id="modal-content"></div>
      </div>
    </div>
  </div>

  <script>
    const readmes = {{
{readmes_json_entries}
    }};

    function showReadme(name) {{
      const md = readmes[name] || '_README não encontrado._';
      document.getElementById('modal-title').textContent = name;
      document.getElementById('modal-gh-link').href = `https://github.com/{user}/${{name}}`;
      document.getElementById('modal-content').innerHTML = marked.parse(md);
      document.getElementById('modal').classList.add('open');
      document.body.style.overflow = 'hidden';
    }}

    function closeModal() {{
      document.getElementById('modal').classList.remove('open');
      document.body.style.overflow = '';
    }}

    function closeOnOverlay(e) {{
      if (e.target === document.getElementById('modal')) closeModal();
    }}

    document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});

    function filterCards(btn) {{
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const lang = btn.dataset.lang;
      document.querySelectorAll('.card').forEach(c => {{
        c.classList.toggle('hidden', lang !== 'all' && c.dataset.lang !== lang);
      }});
    }}
  </script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"✅ {len(repos)} repositórios com README embutido. index.html gerado.")
