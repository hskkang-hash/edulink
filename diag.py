import re
from collections import Counter

content = open("frontend/index.html", encoding="utf-8-sig").read()
ids = re.findall(r'id=["\']([^"\']+)["\']', content)
c = Counter(ids)
dups = {k: v for k, v in c.items() if v > 1}
print("File size:", len(content))
print("Duplicate IDs:", dups)

keys = ["preloginBar","preloginLangBtn","preloginThemeBtn",
        "langToggleBtn","themeToggleBtn","loginBtn","registerBtn","openSignupFlowBtn"]
for k in keys:
    print(f"  {k}: {c.get(k, 0)}")

bar_pos = content.find('id="preloginBar"')
script_pos = content.rfind("<script>")
print(f"preloginBar div at char {bar_pos}")
print(f"<script> tag at char {script_pos}")
print(f"preloginBar BEFORE script: {bar_pos < script_pos}")

# Check hideSections and showSections for preloginBar references
hide_idx = content.find("function hideSections")
show_idx = content.find("function showSections")
print(f"\nhideSections function at char {hide_idx}")
print(f"showSections function at char {show_idx}")

hide_block = content[hide_idx:hide_idx+600]
show_block = content[show_idx:show_idx+600]
print("\n--- hideSections snippet ---")
print(hide_block)
print("\n--- showSections snippet ---")
print(show_block[:400])
