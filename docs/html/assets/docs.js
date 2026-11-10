(() => {
  const body = document.body;

  /* ------------------------------------------------------------------ */
  /* Menú móvil                                                          */
  /* ------------------------------------------------------------------ */
  const menu = document.querySelector('[data-menu]');
  const scrim = document.querySelector('[data-scrim]');

  const setNav = (open) => {
    body.classList.toggle('nav-open', open);
    menu?.setAttribute('aria-expanded', String(open));
    if (scrim) scrim.hidden = !open;
  };

  menu?.addEventListener('click', () => setNav(!body.classList.contains('nav-open')));
  scrim?.addEventListener('click', () => setNav(false));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setNav(false);
  });
  window.addEventListener('resize', () => {
    if (window.innerWidth > 1024) setNav(false);
  });

  /* ------------------------------------------------------------------ */
  /* Filtro del índice                                                   */
  /* ------------------------------------------------------------------ */
  const filter = document.querySelector('[data-nav-filter]');

  filter?.addEventListener('input', () => {
    const query = filter.value.trim().toLowerCase();
    document.querySelectorAll('.nav-link').forEach((link) => {
      const haystack = `${link.textContent} ${link.dataset.keywords || ''}`.toLowerCase();
      link.hidden = Boolean(query) && !haystack.includes(query);
    });
  });

  filter?.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      filter.value = '';
      filter.dispatchEvent(new Event('input'));
    }
  });

  /* ------------------------------------------------------------------ */
  /* Botón copiar en bloques de código                                   */
  /* ------------------------------------------------------------------ */
  document.querySelectorAll('.prose pre').forEach((pre) => {
    if (pre.closest('.mermaid')) return;

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy';
    button.textContent = 'Copiar';
    button.addEventListener('click', async () => {
      const code = pre.querySelector('code') || pre;
      const original = button.textContent;
      try {
        await navigator.clipboard.writeText(code.innerText);
        button.textContent = 'Copiado';
      } catch {
        button.textContent = 'No disponible';
      }
      setTimeout(() => {
        button.textContent = original;
      }, 1400);
    });
    pre.appendChild(button);
  });

  /* ------------------------------------------------------------------ */
  /* Índice activo según scroll                                          */
  /* ------------------------------------------------------------------ */
  const tocLinks = [...document.querySelectorAll('.toc a[href^="#"]')];

  if (tocLinks.length) {
    const byId = new Map(
      tocLinks.map((link) => {
        const href = link.getAttribute('href').slice(1);
        let id = href;
        try {
          id = decodeURIComponent(href);
        } catch {
          /* href ya decodificado */
        }
        return [id, link];
      }),
    );

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          tocLinks.forEach((link) => link.classList.remove('is-active'));
          byId.get(entry.target.id)?.classList.add('is-active');
        });
      },
      { rootMargin: '-84px 0px -72% 0px', threshold: 0 },
    );

    document
      .querySelectorAll('.prose h2[id], .prose h3[id]')
      .forEach((heading) => observer.observe(heading));
  }

  /* ------------------------------------------------------------------ */
  /* Diagramas Mermaid                                                   */
  /* ------------------------------------------------------------------ */
  const blocks = [...document.querySelectorAll('.mermaid')];
  if (!blocks.length) return;

  const showSource = (element) => {
    const pre = document.createElement('pre');
    pre.textContent = element.textContent.trim();
    element.replaceWith(pre);
  };

  if (!window.mermaid) {
    blocks.forEach(showSource);
    return;
  }

  window.mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    theme: 'base',
    fontFamily: 'Inter, system-ui, sans-serif',
    themeVariables: {
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: '14px',
      primaryColor: '#e5eeff',
      primaryTextColor: '#0b1c30',
      primaryBorderColor: '#0051d5',
      secondaryColor: '#dce9ff',
      tertiaryColor: '#f8f9ff',
      mainBkg: '#ffffff',
      nodeBorder: '#0051d5',
      clusterBkg: '#f6f8ff',
      clusterBorder: '#c5c5d3',
      lineColor: '#5b6475',
      textColor: '#0b1c30',
      edgeLabelBackground: '#ffffff',
      actorBkg: '#e5eeff',
      actorBorder: '#0051d5',
      actorTextColor: '#0b1c30',
      signalColor: '#444651',
      signalTextColor: '#0b1c30',
      labelBoxBkgColor: '#e5eeff',
      labelBoxBorderColor: '#0051d5',
      noteBkgColor: '#ffdf9b',
      noteTextColor: '#261a00',
      noteBorderColor: '#7a5900',
    },
    flowchart: { htmlLabels: true, curve: 'basis', padding: 12 },
    sequence: { useMaxWidth: true, mirrorActors: false, messageAlign: 'center' },
    er: { useMaxWidth: true },
  });

  (async () => {
    for (const block of blocks) {
      try {
        await window.mermaid.run({ nodes: [block] });
      } catch (error) {
        console.error('Mermaid:', error);
        showSource(block);
      }
    }
  })();
})();
