"""Builds the animated outfit figure as a standalone SVG string."""
from xml.sax.saxutils import escape

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -20 240 380" width="240" height="380">
<style>
  [data-k] { display: none; }
  __SHOW_CSS__
  .tee{fill:#56B4E9} .long{fill:#009E73} .jacket{fill:#0072B2} .coat{fill:#34495e}
  .rain{fill:#F0E442} .scarf{fill:#E69F00} .beanie{fill:#D55E00} .cap{fill:#CC79A7}
  .glove{fill:#E69F00} .trousers{fill:#3d4a5c} .shorts{fill:#8a9a5b} .boots{fill:#5c3d2e}
  .shoes{fill:#2b2b2b} .umb{fill:#D55E00} .skin{fill:#e0ac82} .hair{fill:#3b2a20}
  .bob { animation: bob 1.8s ease-in-out infinite; }
  @keyframes bob { 50% { transform: translateY(-3px); } }
  #armL { transform-origin: 90px 106px; animation: swing 1.8s ease-in-out infinite; }
  @keyframes swing { 0%,100% { transform: rotate(5deg); } 50% { transform: rotate(-5deg); } }
  #tail { transform-origin: 129px 100px; animation: sway 1.4s ease-in-out infinite; }
  @keyframes sway { 0%,100% { transform: rotate(5deg); } 50% { transform: rotate(-7deg); } }
</style>
<rect x="0" y="-20" width="240" height="380" rx="16" fill="#dbeaf5"/>
<ellipse cx="120" cy="322" rx="46" ry="7" fill="rgba(0,0,0,.18)"/>
<g class="bob">
  <rect class="skin" x="101" y="186" width="17" height="104" rx="8"/>
  <rect class="skin" x="122" y="186" width="17" height="104" rx="8"/>
  <g data-k="shoes"><ellipse class="shoes" cx="108" cy="294" rx="13" ry="7"/><ellipse class="shoes" cx="131" cy="294" rx="13" ry="7"/></g>
  <g data-k="trousers"><rect class="trousers" x="100" y="186" width="19" height="104" rx="8"/><rect class="trousers" x="121" y="186" width="19" height="104" rx="8"/></g>
  <g data-k="shorts"><rect class="shorts" x="100" y="186" width="19" height="44" rx="8"/><rect class="shorts" x="121" y="186" width="19" height="44" rx="8"/></g>
  <g data-k="boots"><rect class="boots" x="97" y="268" width="23" height="28" rx="7"/><rect class="boots" x="120" y="268" width="23" height="28" rx="7"/></g>

  <rect class="skin" x="113" y="84" width="14" height="20" rx="5"/>
  <rect data-k="tshirt" class="tee" x="91" y="100" width="58" height="94" rx="12"/>
  <rect data-k="longsleeve" class="long" x="91" y="100" width="58" height="94" rx="12"/>
  <g data-k="jacket"><rect class="jacket" x="86" y="98" width="68" height="102" rx="12"/><path d="M120 104V198" stroke="rgba(255,255,255,.55)" stroke-width="2"/></g>
  <g data-k="coat"><rect class="coat" x="84" y="98" width="72" height="146" rx="12"/><path d="M120 104V244" stroke="rgba(255,255,255,.45)" stroke-width="2"/><circle cx="113" cy="140" r="2.5" fill="#fff"/><circle cx="113" cy="170" r="2.5" fill="#fff"/></g>
  <g data-k="raincoat"><rect class="rain" x="84" y="98" width="72" height="134" rx="12"/><path d="M98 102 Q120 84 142 102 L142 110 L98 110Z" class="rain" stroke="rgba(0,0,0,.2)"/><path d="M120 108V232" stroke="rgba(0,0,0,.25)" stroke-width="2"/></g>
  <g data-k="scarf"><rect class="scarf" x="104" y="90" width="32" height="15" rx="7"/><g id="tail"><rect class="scarf" x="123" y="98" width="13" height="42" rx="5"/></g></g>

  <circle class="skin" cx="120" cy="66" r="23"/>
  <path class="hair" d="M97 64 Q95 40 120 40 Q145 40 143 64 Q135 52 120 52 Q105 52 97 64Z"/>
  <circle cx="111" cy="69" r="2.2" fill="#1b2430"/><circle cx="129" cy="69" r="2.2" fill="#1b2430"/>
  <path d="M112 78 Q120 84 128 78" fill="none" stroke="#1b2430" stroke-width="2" stroke-linecap="round"/>
  <g data-k="sunglasses" fill="#1b2430"><rect x="103" y="62" width="16" height="10" rx="4"/><rect x="121" y="62" width="16" height="10" rx="4"/><rect x="118" y="65" width="4" height="2"/></g>
  <g data-k="beanie"><path class="beanie" d="M96 62 Q96 34 120 34 Q144 34 144 62Z"/><rect class="beanie" x="94" y="55" width="52" height="10" rx="5" stroke="rgba(0,0,0,.2)"/><circle class="beanie" cx="120" cy="32" r="6"/></g>
  <g data-k="cap"><path class="cap" d="M97 60 Q99 36 122 38 Q143 38 143 60Z"/><path class="cap" d="M138 56 L170 61 L140 65Z" stroke="rgba(0,0,0,.2)"/></g>

  <g id="armL">
    <rect class="skin" x="76" y="102" width="15" height="68" rx="7.5"/>
    <rect data-k="tshirt" class="tee" x="75" y="101" width="17" height="28" rx="7"/>
    <rect data-k="longsleeve" class="long" x="75" y="101" width="17" height="66" rx="7"/>
    <rect data-k="jacket" class="jacket" x="73" y="100" width="20" height="70" rx="8"/>
    <rect data-k="coat" class="coat" x="72" y="100" width="21" height="74" rx="8"/>
    <rect data-k="raincoat" class="rain" x="72" y="100" width="21" height="74" rx="8"/>
    <circle data-k="gloves" class="glove" cx="83.5" cy="173" r="8.5"/>
  </g>
  <g id="armR">
    <rect class="skin" x="149" y="102" width="15" height="68" rx="7.5"/>
    <rect data-k="tshirt" class="tee" x="148" y="101" width="17" height="28" rx="7"/>
    <rect data-k="longsleeve" class="long" x="148" y="101" width="17" height="66" rx="7"/>
    <rect data-k="jacket" class="jacket" x="147" y="100" width="20" height="70" rx="8"/>
    <rect data-k="coat" class="coat" x="147" y="100" width="21" height="74" rx="8"/>
    <rect data-k="raincoat" class="rain" x="147" y="100" width="21" height="74" rx="8"/>
    <circle data-k="gloves" class="glove" cx="156.5" cy="173" r="8.5"/>
  </g>

  <g data-k="umbrella">
    <path d="M156.5 172 V30" stroke="#444" stroke-width="3" stroke-linecap="round"/>
    <path class="umb" d="M96 38 Q156 -32 216 38 Q196 26 186 38 Q171 26 156 38 Q141 26 126 38 Q116 26 96 38Z" stroke="rgba(0,0,0,.2)"/>
  </g>
</g>
<text x="120" y="346" text-anchor="middle" font-family="system-ui, sans-serif" font-size="12" fill="#1b2430">__CAPTION__</text>
</svg>
"""

KNOWN_ITEMS = {"tshirt", "longsleeve", "shorts", "trousers", "jacket", "coat", "raincoat",
               "scarf", "beanie", "cap", "gloves", "sunglasses", "boots", "umbrella"}


def render_svg(items: list[str], caption: str = "") -> str:
    """Returns the figure as an SVG string wearing only the given items."""
    show = {i for i in items if i in KNOWN_ITEMS}
    if "boots" not in show:
        show.add("shoes")
    css = " ".join(f'[data-k="{k}"] {{ display: inline; }}' for k in sorted(show))
    return SVG_TEMPLATE.replace("__SHOW_CSS__", css).replace("__CAPTION__", escape(caption))
