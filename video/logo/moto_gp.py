def moto_svg(c, ring, w, vetro, motore, bg):
    # c scocca, ring cerchi/casco, vetro parabrezza, motore tono intermedio, bg colore di sfondo per staccare le parti
    s=f'stroke="{bg}" stroke-width="3" stroke-linejoin="round"'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="8 26 284 118" width="{w}" height="{round(w*118/284)}">
<path d="M118 100 L62 106" stroke="{c}" stroke-width="10" stroke-linecap="round"/>
<path d="M244 108 L208 58" stroke="{c}" stroke-width="8" stroke-linecap="round"/>
<path d="M120 106 L50 96" stroke="#9d9da8" stroke-width="8" stroke-linecap="round"/>
<g fill="{c}"><circle cx="62" cy="106" r="34"/><circle cx="244" cy="108" r="32"/></g>
<g fill="none" stroke="{ring}" stroke-width="5"><circle cx="62" cy="106" r="20"/><circle cx="244" cy="108" r="19"/></g>
<g fill="#e8352f"><circle cx="62" cy="106" r="6"/><circle cx="244" cy="108" r="6"/></g>
<path d="M116 84 L178 82 L190 110 L124 114 Z" fill="{motore}" {s}/>
<path d="M38 58 L154 62 L162 86 L116 94 Q68 88 38 58 Z" fill="{c}" {s}/>
<path d="M174 68 L206 54 Q238 60 270 92 Q276 100 266 104 L198 114 Q176 108 168 92 Z" fill="{c}" {s}/>
<path d="M182 90 L262 94" stroke="#e8352f" stroke-width="5" stroke-linecap="round"/>
<path d="M238 82 L264 76 L267 83 L244 90 Z" fill="#e8352f" {s}/>
<path d="M202 56 L224 54 L232 60 L210 64 Z" fill="{vetro}"/>
<path d="M110 76 Q130 58 172 52 L198 56 L194 72 Q160 76 126 88 Z" fill="#e8352f" {s}/>
<path d="M186 60 L216 68" stroke="#e8352f" stroke-width="8" stroke-linecap="round"/>
<path d="M124 86 Q150 108 178 100" fill="none" stroke="#e8352f" stroke-width="10" stroke-linecap="round"/>
<circle cx="208" cy="44" r="13" fill="#f4f4f6" stroke="{c}" stroke-width="3"/><path d="M210 40 h13 v8 h-13 z" fill="{c}"/>
</svg>'''
