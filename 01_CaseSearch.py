"""
Overall Scraper
"""

from playwright.async_api import async_playwright
import asyncio
import time
import os
from dotenv import load_dotenv

load_dotenv()

## URL to the Case Search system in the NE Justice Website
url = os.environ["url"]

## The three counties of concern
counties = ["Douglas", "Lancaster", "Sarpy"]

## TODO: Set time range, currently set to scrape 2025 (updated 2025-04-19)
years = [str(x) for x in range(2025, 2026)]

i = 0

## Async run
async def run():

    # Iterating through county and year
    for county in counties:

        for year in years:

            async with async_playwright() as p:

                ## Call chromium to specified URL
                browser = await p.chromium.launch(headless = False)
                page = await browser.new_page()
                await page.goto(url)
                
                ## Select county
                await page.locator("div#county_num_chosen").click()
                await page.locator("div#county_num_chosen").get_by_text(county).click()

                ## Choose all courts
                await page.locator("div#court_type_chosen").click()
                await page.locator("div#court_type_chosen").get_by_text("All Court Types").click()

                ## Only Juvenile Cases
                await page.locator("div#case_type_chosen").click()
                await page.locator("div#case_type_chosen").get_by_text("Juvenile").click()

                ## Consider all judges
                await page.locator("div#judge_chosen").click()
                await page.locator("div#judge_chosen").get_by_text("All Judges").click()

                ## Select all attorneys too
                await page.locator("div#attorney_name_chosen").click()
                await page.locator("div#attorney_name_chosen").get_by_text("All Attorneys").click()

                ## Select specified year
                await page.select_option("select#year", value = [year])

                ## Sort in descending order of CaseNum (the first entry should be the latets)
                await page.select_option("select#sort", value = ["casenum"])
                await page.locator("label", has_text = "Descending").click()
                
                ## Search and sleep (to make sure it loads)
                await page.get_by_role("button", name = "search").click()
                time.sleep(3)
                
                ## Check if any results are returned, if not pass
                no_results = await page.locator("div#info.alert.alert-info").is_visible()

                if no_results:
                    pass

                else: ## If there are results

                    page_number = 0

                    ## Save the HTML of the search results
                    html = await page.content()
                    page_name = f"{county}_{year}_{str(page_number)}"
                    
                    ## Write them at CaseSearchAll
                    with open(f"./CaseSearchAll/{page_name}.html", "w") as f:
                        f.write(html)

                    ## Check if there is a "next" button. If so, we want to iterate through
                    ## all of it
                    has_next = await page.locator("div#page_links.text-center").locator("li", has_text = "Next").is_visible()

                    ## While there is a next button, rinse and repeat
                    while(has_next):
                        
                        ## Click next, and wait for loading
                        await page.locator("div#page_links.text-center").locator("li", has_text = "Next").click()
                        time.sleep(2)

                        page_number = page_number + 1

                        html = await page.content()
                        
                        page_name = f"{county}_{year}_{str(page_number)}"
                    
                        with open(f"./CaseSearchAll/{page_name}.html", "w") as f:
                            f.write(html)

                        has_next = await page.locator("div#page_links.text-center").locator("li", has_text = "Next").is_visible()


            await browser.close()


async def main():   

    await run()

asyncio.run(main())