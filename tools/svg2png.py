import asyncio, sys
from playwright.async_api import async_playwright
async def main(svg, out, w):
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(device_scale_factor=1)
        data = open(svg).read()
        await pg.set_content(f'<html><body style="margin:0;background:transparent">{data}</body></html>')
        await pg.evaluate(f"""()=>{{const s=document.querySelector('svg'); const vb=s.viewBox.baseVal; s.setAttribute('width',{w}); s.setAttribute('height',{w}*vb.height/vb.width); s.style.display='block';}}""")
        el = await pg.query_selector('svg')
        await el.screenshot(path=out, omit_background=True)
        await b.close()
asyncio.run(main(sys.argv[1], sys.argv[2], int(sys.argv[3])))
