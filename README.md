**Analysis Report Generator**

Automate stock analysis using Python, financial data, and AI (Gemini). Easily generate PDF or HTML reports with just one command!

**🗂️ Project Structure**

The project includes 4 main files:

| File          | Description                                                                |
| ------------- | -------------------------------------------------------------------------- |
| `main.py`     | Core script for data processing & analysis. Outputs results to `data.json` |
| `data.json`   | Stores processed data from `main.py`, used for report generation           |
| `report.html` | HTML template for the report (tables, charts...). Viewable via Live Server |
| `save.py`     | Automatically generates a PDF report without running each step manually    |

**Getting Started**

1. Install required libraries

2. Configure the project

   Update stock symbol (variable symbol).

   Adjust Excel file paths in main.py to match your local directories.

3. Running the Project

Option 1: View HTML report
   
   Open report.html in VS Code
   
   Use the Live Server extension

Option 2: Auto-generate PDF through save.py. The report will be saved as [stock_code].pdf in the root folder

**Key Features**
- Gemini AI: Automatically generates market, sector, and stock insights
- Interactive charts: Prebuilt and rendered in HTML
- vnstock API integration: Fetches additional stock data online

**Preview**

![image](https://github.com/user-attachments/assets/d1df70b5-a9f8-4bfa-bb40-6e7c55007552)

**Libraries Used**
- vnstock, pandas-ta, pandas, json
- google-generativeai
- pyppeteer, asyncio, os

**Contributing**

Feel free to open issues or submit a pull request for bug fixes or feature suggestions.

**License**

Distributed under the MIT License.
