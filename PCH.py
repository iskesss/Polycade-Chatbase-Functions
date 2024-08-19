import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import html2text

# for Docker compatability
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# for Google Sheets compatability
import gspread
from icecream import ic
from google.oauth2.service_account import Credentials
from gspread import Spreadsheet

chrome_options = Options()
# apparently --no-sandbox is dangerous lmao
chrome_options.add_argument("--no-sandbox")
# basically just means it's going to run without a screen
chrome_options.add_argument("--headless")
# circumvents memory constraints in containerized environments by using /tmp (yes, a disk folder) as memory. slower but more reliable for docker.
chrome_options.add_argument("--disable-dev-shm-usage")


def pause() -> None:
    pause_time = random.uniform(5, 10)
    print(f"> Pausing for {round(pause_time,1)}s to prevent ratelimit")
    time.sleep(pause_time)


class PolycadeChatbaseHelper:
    # fyi: qna means Q&A
    def __init__(self) -> None:
        return

    def get_qna_spreadsheet(self) -> Spreadsheet:
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        POLYCADE_QNA_SHEET_ID = "1nVZM28NEdcQjGw_qwnNxMeJ16kOGh1xuseCBQlOdgIY"

        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        client = gspread.authorize(creds)

        return client.open_by_key(POLYCADE_QNA_SHEET_ID)

    def fetch_helpcenter_subpage_links(self) -> list[(str, str)]:
        """
        Scrapes the main Polycade Help Center webpage and retrieves a link to each subpage containing a Q&A.

        Args:
            None

        Returns:
            list[(str,str)] : A list of pairs, each of which contains... (a_helpcenter_question,the_corresponding_http_link)
        """
        # driver = webdriver.Chrome()
        driver = webdriver.Chrome(  # surely we don't have to reinstall ChromeDriverManager every time?
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )
        driver.get("https://polycade.com/pages/helphq-2#/")

        print("> Loading Polycade Help Center")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".collections-list-item"))
        )
        helpcenter_code = driver.page_source
        driver.quit()  # TODO: Maybe get rid of this and you won't have to redeclare drivers every time

        # Parse the HTML content
        soup = BeautifulSoup(helpcenter_code, "html.parser")

        # Find all <li> elements with class "collections-list-item". question_link_code_snippets is a set of HTML code snippets for each external link in the help center.
        question_link_code_snippets = soup.find_all(
            "li", class_="collections-list-item"
        )

        print(f"> {len(question_link_code_snippets)} Q&A links found:")

        question_link_pairs = []

        for i in range(0, len(question_link_code_snippets)):
            # truncate '<li class="collections-list-item><a href="' from the front
            trimmed_snippet = str(question_link_code_snippets[i])[43:]
            link = ""
            c = 0
            while trimmed_snippet[c] != ">":
                link += trimmed_snippet[c]
                c += 1
            c += 1

            question = ""
            while trimmed_snippet[c] != "<":
                question += trimmed_snippet[c]
                c += 1

            print(f"\t{i+1}. {question}")

            question_link_pairs.append(
                (question, "https://polycade.com/pages/helphq-2" + link)
            )
        return question_link_pairs

    def parse_qna_subpages(
        self, question_link_pairs: list[(str, str)]
    ) -> list[(str, str)]:
        """
        Parses Q&A subpages to extract answers.

        Args:
            question_link_pairs (list[(str,str)]) : A list of pairs, each of which contains... (a_helpcenter_question,the_corresponding_http_link)

        Returns:
            list[(str,str)] : A list of pairs, each of which contains... (a_helpcenter_question,the_appropriate_answer)
        """

        # one by one we'll overwrite the links with answers
        question_answer_pairs = question_link_pairs
        print("> This is gonna take a while.")

        for i in range(0, len(question_link_pairs)):
            pause()  # to prevent ratelimiting

            # driver = webdriver.Chrome()
            driver = webdriver.Chrome(  # surely we don't have to reinstall ChromeDriverManager every time?
                service=Service(ChromeDriverManager().install()), options=chrome_options
            )

            driver.get(question_link_pairs[i][1])  # get the link
            print(f"> Parsing subpage {i+1}/{len(question_link_pairs)}")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".content-wrap"))
            )
            qna_code = driver.page_source
            driver.quit()  # TODO: Maybe get rid of this and you won't have to redeclare drivers every time

            # Parse the HTML content
            soup = BeautifulSoup(qna_code, "html.parser")

            # Find a <div> element with class ".content-wrap". answer_code_snippet is an HTML code snippet which contains the answer to the current question
            answer_code_snippet = soup.find("div", class_="content-wrap")

            # Removing js and css code
            for script in answer_code_snippet.find_all(["script", "style"]):
                script.extract()

            # Extract text in markdown format
            answer_code_snippet = str(answer_code_snippet)  # convert to str

            html2text_instance = html2text.HTML2Text()
            html2text_instance.images_to_alt = True
            html2text_instance.body_width = 0
            html2text_instance.single_line_break = True
            answer = html2text_instance.handle(answer_code_snippet)

            # replace the current question's link with it's answer (in Markdown format)
            question_answer_pairs[i] = (question_answer_pairs[i][0], answer)

        return question_answer_pairs

    def write_qnas_to_sheets(self, question_answer_pairs: list[(str, str)]) -> None:
        """
        Sends an arbitrary amount of Polycade Q&As to Google Sheets.

        Args:
            question_answer_pairs (list[(str, str)]) : A list of pairs, each of which contains... (a_helpcenter_question,the_appropriate_answer)

        Returns:
            None
        """

        spreadsheet = self.get_qna_spreadsheet()
        worksheet = spreadsheet.worksheet("Scraped from Helpcenter")

        num_rows_to_update = (
            len(question_answer_pairs) + 1
        )  # +1 at the bottom because we're reserving a row for the header

        print(f"> Preparing to update {num_rows_to_update} rows")

        # +1 at the bottom because we're reserving a row for the header
        cells = worksheet.range(name=f"A1:B{num_rows_to_update}")

        # unpack the question_answer_pairs list into a more gspread-friendly format: [Q1,A1,Q2,A2,...Qn,An]
        qaqaqa = []
        for qa in question_answer_pairs:
            qaqaqa.append(qa[0])  # append question
            qaqaqa.append(qa[1])  # append answer

        cells[0].value = "Question"
        cells[1].value = "Answer"

        for i in range(2, len(cells)):
            cells[i].value = qaqaqa[i - 2]

        response = worksheet.update_cells(cell_list=cells)
        print(f"> Google Sheets returned {response}")
        print(f"> Inserting current timestamp")
        worksheet.update_acell(
            label="H2",
            value=f"Last Updated at {datetime.now().strftime('%A %b %d, %Y, %I:%M%p')}",  # TODO: Add the timezone or something. It's always 5 o'clock somewhere!
        )

        return

    def update_sheets_with_qnas(self) -> None:
        print("> Fetching links to Q&A subpages from Polycade Helpcenter")
        question_link_pairs = self.fetch_helpcenter_subpage_links()

        print(
            f"> Parsing all Q&A subpages to which links were found ({len(question_link_pairs)} total)"
        )
        question_answer_pairs = self.parse_qna_subpages(
            question_link_pairs=question_link_pairs
        )  # this takes a loooong time

        print(f"> Writing {len(question_link_pairs)} Q&As to Google Sheets")
        self.write_qnas_to_sheets(question_answer_pairs=question_answer_pairs)

        print("> Sheets have been updated!")
        return

    def download_qnas_from_sheets(self) -> None:
        """
        Compiles the Google Sheets Q&A into a local .txt document which can be drag+dropped onto the Chatbase dashboard.

        Args:
            None

        Returns:
            None
        """
        spreadsheet = self.get_qna_spreadsheet()
        sheets_to_scrape = []
        sheets_to_scrape.append(spreadsheet.worksheet("Scraped from Helpcenter"))
        sheets_to_scrape.append(spreadsheet.worksheet("Manual Entries"))

        all_qaqaqa = (
            []
        )  # a list of all Q&As present in worksheets within sheets_to_scrape. format: [Q1,A1,Q2,A2,...Qn,An]

        for sheet in sheets_to_scrape:
            whole_worksheet_read = False
            window_top = 2
            window_bottom = 100
            num_qnas_found = 0
            print(f"> Scraping '{sheet.title}' sheet...", end=" ")
            # we'll scan down through the worksheet 100 cells at a time, until we encounter empty cells, at which point we'll have read the whole worksheet
            while not whole_worksheet_read:
                cell_batch = sheet.range(name=f"A{window_top}:B{window_bottom}")
                if cell_batch[len(cell_batch) - 1].value == "":  # empty cell at bottom?
                    whole_worksheet_read = True
                    c = 0
                    while c < len(cell_batch) and cell_batch[c].value != "":
                        # forgive the triple nested loop LMAO i really don't think there's another way to do this.
                        all_qaqaqa.append(cell_batch[c].value)
                        num_qnas_found += 0.5
                        c += 1
                else:  # cell_batch is completely full of qnas, so just add the entire thing to all_qaqaqa and we'll shift the window down (to go find more qnas)
                    print(f"clearly we need more than {window_bottom}")
                    for cell in cell_batch:
                        all_qaqaqa.append(cell.value)
                        num_qnas_found += 0.5
                    window_top = window_bottom + 1
                    window_bottom += 100

            # all_qaqaqa SHOULD NEVER BE ODD, as that would mean there's either 1) a question without an answer or 2) an answer without a question
            assert len(all_qaqaqa) % 2 == 0
            print(f"found {round(num_qnas_found)} Q&As")

        print(f"> Concluded with {round(len(all_qaqaqa) / 2)} questions total")

        is_containerized = os.environ.get(
            key="AM_I_IN_A_DOCKER_CONTAINER", default=False
        )
        if is_containerized:
            print(
                "> Docker environment detected. Generating .txt file in /downloads...",
                end=" ",
            )
            output_dir = "/downloads"
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.join(
                output_dir,
                f"All entries from Google Sheet at {datetime.now().strftime('%A %b %d, %Y, %I;%M%p')}.txt",
            )
        else:
            print(
                f"> Docker Environment not detected. Generating .txt file in CWD...",
                end=" ",
            )
            filename = f"All entries from Google Sheet at {datetime.now().strftime('%A %b %d, %Y, %I;%M%p')}.txt"

        outfile = open(filename, "w")
        for i in range(0, len(all_qaqaqa)):
            if i % 2 == 0:  # all_qaqaqa[i] is a question
                outfile.write(
                    f"# {all_qaqaqa[i]}\n"
                )  # add '#' to simulate a markdown header so each Q&A is more clearly defined
            else:  # all_qaqaqa[i] is the answer corresponding to all_qaqaqa[i-1]
                outfile.write(f"{all_qaqaqa[i]}\n\n")

        outfile.close()
        print("done!")
        return "success"


# -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_

# pch = PolycadeChatbaseHelper()

# pch.download_qnas_from_sheets()

# smalltemp = [
#     (
#         "How many games come with Polycade?",
#         'https://polycade.com/pages/helphq-2#/collection/2971/article/11884"',
#     ),
#     (
#         "What is needed to install a Polycade?",
#         'https://polycade.com/pages/helphq-2#/collection/2971/article/11885"',
#     ),
#     (
#         "What are the specs?",
#         'https://polycade.com/pages/helphq-2#/collection/2971/article/11887"',
#     )
# ]

# pch.write_qnas_to_sheets(question_answer_pairs=bigtemp)

# output = pch.parse_qna_subpages(temp)

# outfile = open("qna_output.txt", "w")

# for i in range(0, len(output)):
#     outfile.write("-------------------------------\n")
#     outfile.write(f"{i+1}. {output[i][0]}\n")
#     outfile.write("-------------------------------\n")
#     outfile.write(output[i][1])
# outfile.close()
