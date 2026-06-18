import os

files = ['dashboard1_strategic.html', 'dashboard2_analytical.html']
for f in files:
    path = os.path.join(r'c:\Users\elisa\Desktop\KEMV-FINALFINAL\Austria_Energy_Capstone\Capstone3\templates', f)
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    content = content.replace('background:#1D4ED8', 'background:#0284C7')
    content = content.replace('background:#059669', 'background:#0D9488')
    content = content.replace('background:#B45309', 'background:#F59E0B')
    content = content.replace('background:#78350F', 'background:#65A30D')
    content = content.replace('background:#374151', 'background:#1F2937')
    content = content.replace('background:#B91C1C', 'background:#7C3AED')
    content = content.replace('background:#78350F" style="opacity:0.6"', 'background:#991B1B"')
    
    with open(path, 'w', encoding='utf-8') as file:
        file.write(content)

js_path = r'c:\Users\elisa\Desktop\KEMV-FINALFINAL\Austria_Energy_Capstone\Capstone3\static\js\charts.js'
with open(js_path, 'r', encoding='utf-8') as file:
    js_content = file.read()

js_content = js_content.replace("'#1D4ED8',  // deep blue  (water)", "'#0284C7',  // Sky Blue (water)")
js_content = js_content.replace("'#059669',  // emerald    (growth)", "'#0D9488',  // Teal (airy)")
js_content = js_content.replace("'#B45309',  // amber-dark (sun, readable on white)", "'#F59E0B',  // Amber (sun)")
js_content = js_content.replace("'#78350F',  // brown      (organic)", "'#65A30D',  // Lime (plants)")
js_content = js_content.replace("'#374151',  // slate-dark (carbon)", "'#1F2937',  // Dark Gray (coal)")
js_content = js_content.replace("'#B91C1C',  // dark red   (combustion)", "'#7C3AED',  // Purple (gas)")
js_content = js_content.replace("'#92400E',  // dark orange-brown (fossil)", "'#991B1B',  // Dark Red (oil)")

with open(js_path, 'w', encoding='utf-8') as file:
    file.write(js_content)
