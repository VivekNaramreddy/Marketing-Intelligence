"""Optional browser smoke check. Run against a disposable database, not user data."""
import os
from pathlib import Path
from time import time

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'artifacts'
ARTIFACTS.mkdir(exist_ok=True)

with sync_playwright() as p:
    chrome = os.getenv('BROWSER_EXECUTABLE', r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    browser = p.chromium.launch(executable_path=chrome, headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1050})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:5173')
    expect(page.get_by_role('button', name='New workspace')).to_be_enabled()
    if page.get_by_text('A clearer view of your marketing.', exact=True).is_visible():
        page.get_by_label('Your first workspace').fill(f'Browser QA {int(time())}')
        page.get_by_role('button', name='Create workspace', exact=True).click()
    else:
        page.get_by_role('button', name='New workspace').click()
        page.get_by_label('Workspace name', exact=True).fill(f'Browser QA {int(time())}')
        page.get_by_role('button', name='Create', exact=True).click()
    page.get_by_role('button', name='Load demo dataset').click()
    expect(page.get_by_role('button', name='Analyze selected brands')).to_be_enabled()
    page.get_by_role('button', name='Analyze selected brands').click()
    expect(page.get_by_text('18,551', exact=True).first).to_be_visible()
    expect(page.get_by_role('heading', name='Instagram engagement gap')).to_be_visible()
    page.locator('summary').filter(has_text='View evidence').first.click()
    expect(page.get_by_text('Competitor average:', exact=False).first).to_be_visible()
    page.locator('summary').filter(has_text='View evidence').first.click()
    page.screenshot(path=str(ARTIFACTS / 'dashboard-desktop.png'), full_page=True)
    page.get_by_role('button', name='Analysis', exact=True).click()
    page.get_by_role('tab', name='Competitors').click()
    page.get_by_label('Platform', exact=True).select_option('Instagram')
    expect(page.locator('tbody tr')).to_have_count(5)
    page.get_by_role('tab', name='Content').click()
    expect(page.get_by_text('The next layer of the story.')).to_be_visible()
    page.get_by_role('button', name='Reports', exact=True).click()
    page.get_by_role('button', name='Generate Basic Report', exact=True).first.click()
    expect(page.get_by_role('heading', name='Executive Summary')).to_be_visible()
    expect(page.get_by_role('heading', name='Recommendations', exact=True)).to_be_visible()
    page.screenshot(path=str(ARTIFACTS / 'report-desktop.png'), full_page=True)
    page.get_by_role('button', name='Data', exact=True).click()
    page.get_by_role('tab', name='Manual entry').click()
    page.get_by_label('Brand', exact=True).fill('QA Competitor')
    page.get_by_label('followers', exact=True).fill('150')
    page.get_by_role('button', name='Add observation').click()
    expect(page.locator('table').get_by_text('QA Competitor', exact=True)).to_be_visible()
    page.get_by_role('button', name='Dashboard', exact=True).click()
    expect(page.get_by_text('18,551', exact=True).first).to_be_visible()
    page.set_viewport_size({'width': 390, 'height': 844})
    page.screenshot(path=str(ARTIFACTS / 'dashboard-mobile.png'), full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile page overflows horizontally'
    page.set_viewport_size({'width': 820, 'height': 1180})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Tablet page overflows horizontally'
    workspace_name = page.locator('#workspace option:checked').inner_text()
    page.reload()
    expect(page.locator('#workspace')).to_be_enabled()
    page.locator('#workspace').select_option(label=workspace_name)
    expect(page.get_by_role('heading', name='Good intelligence starts with good data.')).to_be_visible()
    expect(page.locator('table').get_by_text('QA Competitor', exact=True)).to_be_visible()
    assert not errors, errors
    browser.close()
    print('Browser smoke passed: workspace, demo, dashboard, evidence, comparison filter, content placeholder, report, manual entry, persistence, and mobile/tablet layout. No browser errors.')
