from playwright.async_api import async_playwright
import asyncio
import time
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ["url"]

counties = ["Douglas", "Lancaster", "Sarpy"]
#subtypes = ["Juvenile-Felony", "Juvenile-Misdemeanor/Infraction", "Juvenile-Status Offender", "Juvenile-Traffic Offense"]

years = [str(x) for x in range(2010, 2025)]

i = 0

async def run():

    for county in counties:

        #for subtype in subtypes:

        for year in years:

            async with async_playwright() as p:

                browser = await p.chromium.launch(headless = False)
                page = await browser.new_page()
                await page.goto(url)
                

                await page.locator("div#county_num_chosen").click()
                await page.locator("div#county_num_chosen").get_by_text(county).click()

                await page.locator("div#court_type_chosen").click()
                await page.locator("div#court_type_chosen").get_by_text("All Court Types").click()

                await page.locator("div#case_type_chosen").click()
                await page.locator("div#case_type_chosen").get_by_text("Juvenile").click()

                #await page.locator("div#subtype_chosen").click()
                #await page.locator("div#subtype_chosen").get_by_text(subtype).click()

                await page.locator("div#judge_chosen").click()
                await page.locator("div#judge_chosen").get_by_text("All Judges").click()

                await page.locator("div#attorney_name_chosen").click()
                await page.locator("div#attorney_name_chosen").get_by_text("All Attorneys").click()

                await page.select_option("select#year", value = [year])

                await page.select_option("select#sort", value = ["casenum"])

                await page.locator("label", has_text = "Descending").click()
                
                await page.get_by_role("button", name = "search").click()

                time.sleep(3)
                #await page.wait_for

                no_results = await page.locator("div#info.alert.alert-info").is_visible()

                if no_results:
                    pass

                else:

                    page_number = 0

                    html = await page.content()

                    #page_name = f"{county}_{subtype.replace('/', '_')}_{year}_{str(page_number)}"
                    page_name = f"{county}_{year}_{str(page_number)}"
                    
                    with open(f"./CaseSearchAll/{page_name}.html", "w") as f:
                        f.write(html)


                    has_next = await page.locator("div#page_links.text-center").locator("li", has_text = "Next").is_visible()


                    while(has_next):

                        await page.locator("div#page_links.text-center").locator("li", has_text = "Next").click()
                        
                        time.sleep(2)

                        page_number = page_number + 1

                        html = await page.content()

                        #page_name = f"{county}_{subtype.replace('/', '_')}_{year}_{str(page_number)}"

                        page_name = f"{county}_{year}_{str(page_number)}"
                    
                        with open(f"./CaseSearchAll/{page_name}.html", "w") as f:
                            f.write(html)

                        has_next = await page.locator("div#page_links.text-center").locator("li", has_text = "Next").is_visible()


            await browser.close()


async def main():   

    await run()

asyncio.run(main())