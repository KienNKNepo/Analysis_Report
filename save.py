# save.py
import asyncio
import os
from pyppeteer import launch
from main import generate_data  # import hàm generate_data từ main.py

# Đặt mã cổ phiếu mới tại đây
symbol = "DBD"
# Gọi hàm generate_data để tạo data.json mới
generate_data(symbol)

async def main():
    browser = await launch(
        executablePath='C:/Program Files/Google/Chrome/Application/chrome.exe',
        args=['--allow-file-access-from-files']
    )
    page = await browser.newPage()
    file_path = f'file://{os.path.abspath("report.html")}'
    await page.goto(file_path, {'waitUntil': 'networkidle2'})
    await page.pdf({
        'path': f'{symbol}.pdf',
        'format': 'A4',
        'printBackground': True
    })
    await browser.close()
    print(f"Báo cáo PDF đã được tạo: {symbol}.pdf")

asyncio.run(main())
