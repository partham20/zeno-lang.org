"""The site's icons: simple line drawings on a 24 by 24 grid, drawn for zeno-lang.org.

Each icon is the inside of an <svg>. `icon(name)` gives the whole element,
sized by CSS (`.icon`) and coloured by `currentColor`.
"""

ICONS = {
    # language
    "type": '<rect x="3.5" y="3.5" width="17" height="17" rx="4"/><path d="M8 8.5h8M12 8.5v8"/>',
    "check": '<path d="M12 3l7.5 3v5.5c0 4.5-3.2 8.2-7.5 9.5-4.3-1.3-7.5-5-7.5-9.5V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    "none": '<circle cx="12" cy="12" r="8.5"/><path d="M6 18L18 6"/>',
    "alert": '<path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17.2v.1"/>',
    "layers": '<path d="M12 3.5l8.5 4.5-8.5 4.5L3.5 8z"/><path d="M3.5 12l8.5 4.5 8.5-4.5M3.5 16l8.5 4.5 8.5-4.5"/>',
    "gauge": '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l4-5.5"/><circle cx="12" cy="17" r="1.3"/>',
    "ruler": '<rect x="2.5" y="8" width="19" height="8" rx="1.5"/><path d="M6.5 8v3M10 8v4.5M13.5 8v3M17 8v4.5"/>',
    "copies": '<rect x="8" y="8" width="12" height="12" rx="2.5"/><path d="M16 8V6.5A2.5 2.5 0 0 0 13.5 4h-7A2.5 2.5 0 0 0 4 6.5v7A2.5 2.5 0 0 0 6.5 16H8"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12l8-8M16 7l2.5 2.5M14 9l2 2"/>',
    "words": '<path d="M4 7h16M4 12h10M4 17h13"/>',
    "braces": '<path d="M9 4H8a2 2 0 0 0-2 2v3.5a2.5 2.5 0 0 1-2.5 2.5A2.5 2.5 0 0 1 6 14.5V18a2 2 0 0 0 2 2h1M15 4h1a2 2 0 0 1 2 2v3.5a2.5 2.5 0 0 0 2.5 2.5 2.5 2.5 0 0 0-2.5 2.5V18a2 2 0 0 1-2 2h-1"/>',
    "function": '<path d="M14.5 4.5c-2.5-.5-4 .5-4.5 3L8 18c-.5 2.2-2 2.7-3.5 2.3M6.5 11h7"/><path d="M15 12l4 6M19 12l-4 6"/>',
    # machines
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx=".8"/><path d="M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3"/>',
    "chip-pin": '<circle cx="12" cy="12" r="3"/><path d="M12 3v4M12 17v4M3 12h4M17 12h4"/>',
    "zap": '<path d="M13 3L5 13.5h6L10 21l8-10.5h-6z"/>',
    "memory": '<rect x="3" y="7" width="18" height="10" rx="2"/><path d="M7 7v10M11 7v10M15 7v10M3 20h18"/>',
    "pool": '<rect x="3.5" y="4" width="17" height="16" rx="2.5"/><path d="M3.5 10h17M3.5 15h17M10 4v16"/>',
    "board": '<rect x="3" y="5" width="18" height="14" rx="2.5"/><circle cx="8" cy="12" r="1.6"/><circle cx="12.5" cy="12" r="1.6"/><path d="M16.5 10.5h2M16.5 13.5h2"/>',
    "terminal": '<rect x="3" y="4.5" width="18" height="15" rx="2.5"/><path d="M7 10l3 2.5L7 15M12.5 15.5H17"/>',
    "code": '<path d="M8.5 7L3.5 12l5 5M15.5 7l5 5-5 5M13.5 4.5l-3 15"/>',
    "tree": '<circle cx="12" cy="5" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/><path d="M12 7v4M12 11l-5.2 5.3M12 11l5.2 5.3"/>',
    "scan": '<path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16M7.5 12h9"/>',
    "play": '<circle cx="12" cy="12" r="8.5"/><path d="M10 8.5l5.5 3.5-5.5 3.5z"/>',
    "stack": '<path d="M5 6h14M5 10h14M5 14h14M5 18h9"/>',
    "c": '<circle cx="12" cy="12" r="8.5"/><path d="M15 9.3a3.8 3.8 0 1 0 0 5.4"/>',
    "dragon": '<path d="M4 19c3-1 4-4 4-7a4 4 0 0 1 8 0c0 3 1 6 4 7"/><path d="M9.5 9.5L7 5M14.5 9.5L17 5"/><circle cx="10.5" cy="12.5" r=".6"/><circle cx="13.5" cy="12.5" r=".6"/>',
    # places
    "book": '<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H11v16H5.5A1.5 1.5 0 0 1 4 18.5zM20 5.5A1.5 1.5 0 0 0 18.5 4H13v16h5.5a1.5 1.5 0 0 0 1.5-1.5z"/>',
    "compass": '<circle cx="12" cy="12" r="8.5"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
    "scale": '<path d="M12 4v16M7 20h10M5 8h14M5 8l-2.5 6a2.5 2.5 0 0 0 5 0zM19 8l-2.5 6a2.5 2.5 0 0 0 5 0z"/>',
    "map": '<path d="M9 4.5L3.5 6.5v13L9 17.5l6 2 5.5-2v-13L15 6.5z"/><path d="M9 4.5v13M15 6.5v13"/>',
    "info": '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8v.1"/>',
    "package": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
    "globe": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.5 2.5 3.5 5.5 3.5 8.5s-1 6-3.5 8.5c-2.5-2.5-3.5-5.5-3.5-8.5s1-6 3.5-8.5z"/>',
    "server": '<rect x="4" y="4" width="16" height="7" rx="2"/><rect x="4" y="13" width="16" height="7" rx="2"/><path d="M8 7.5h.1M8 16.5h.1"/>',
    "chart": '<path d="M4 20V4M4 20h16"/><path d="M8 16l3.5-4 3 2.5L19 9"/>',
    "edit": '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
    "link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "sparkle": '<path d="M12 3c.6 4.2 2.8 6.4 7 7-4.2.6-6.4 2.8-7 7-.6-4.2-2.8-6.4-7-7 4.2-.6 6.4-2.8 7-7z"/><path d="M19 16.5c.3 1.5 1 2.2 2.5 2.5-1.5.3-2.2 1-2.5 2.5-.3-1.5-1-2.2-2.5-2.5 1.5-.3 2.2-1 2.5-2.5z"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "github": '<path d="M9 19c-4 1.3-4-2-6-2.5M15 21v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.3 4.3 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12 12 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.3 4.3 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>',
    "download": '<path d="M12 4v11M7.5 10.5L12 15l4.5-4.5"/><path d="M4.5 16.5v1.5a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-1.5"/>',
    "copy": '<rect x="8.5" y="8.5" width="11" height="11" rx="2"/><path d="M15.5 8.5V6.5a2 2 0 0 0-2-2h-7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h2"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "feather": '<path d="M20 4c-6 0-12 4-13.5 12L5 20M7 16h7c3-1.5 5-5 6-12M9.5 12.5h6.5"/>',
    "loop": '<path d="M17 3l3 3-3 3"/><path d="M20 6H9a5 5 0 0 0-5 5v1M7 21l-3-3 3-3"/><path d="M4 18h11a5 5 0 0 0 5-5v-1"/>',
    "eye": '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
}


def icon(name, cls="icon"):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')
