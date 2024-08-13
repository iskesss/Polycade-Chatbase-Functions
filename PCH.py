from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import html2text


def pause() -> None:
    pause_time = random.uniform(0.5, 5)
    time.sleep(pause_time)


class PolycadeChatbaseHelper:
    # fyi: qna means Q&A
    def __init__(self) -> None:
        return

    def fetch_qna_links_from_helpcenter(self) -> list[(str, str)]:
        """
        Scrapes the main Polycade Help Center webpage and retrieves a link to each subpage containing a Q&A.

        Args:
            None

        Returns:
            list[(str,str)] : A list of pairs, each of which contains... (a_helpcenter_question,the_corresponding_http_link)
        """
        driver = webdriver.Chrome()
        driver.get("https://polycade.com/pages/helphq-2#/")

        print("> Loading Polycade Help Center")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".collections-list-item"))
        )
        helpcenter_code = driver.page_source
        driver.quit()

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

        for i in range(0, len(question_link_pairs)):
            pause()  # to prevent ratelimiting

            driver = webdriver.Chrome()
            driver.get(question_link_pairs[i][1])  # get the link
            print(f"> Parsing subpage {i+1}/{len(question_link_pairs)}")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".content-wrap"))
            )
            qna_code = driver.page_source
            driver.quit()

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

    def send_qnas_to_google_sheets(
        self, question_answer_pairs: list[(str, str)]
    ) -> None:
        """
        Sends an arbitrary amount of Polycade Q&As to Google Sheets.

        Args:
            question_answer_pairs (list[(str, str)]) : A list of pairs, each of which contains... (a_helpcenter_question,the_appropriate_answer)

        Returns:
            None
        """

        return

    def compile_txt(self) -> None:
        # compile the Google Sheet Q&A into a .txt document which can be drag+dropped onto the Chatbase dashboard.
        filename = f"All entries from Google Sheet at {datetime.now().strftime('%A %b %d, %Y, %I;%M%p')}.txt"
        outfile = open(filename, "w")

        outfile.write("content goes here")

        outfile.close()
        return


ingestor = PolycadeChatbaseHelper()

# ingestor.fetch_qna_links_from_helpcenter()
temp = [
    (
        "How many games come with Polycade?",
        'https://polycade.com/pages/helphq-2#/collection/2971/article/11884"',
    ),
    (
        "What is needed to install a Polycade?",
        'https://polycade.com/pages/helphq-2#/collection/2971/article/11885"',
    ),
    (
        "What are the specs?",
        'https://polycade.com/pages/helphq-2#/collection/2971/article/11887"',
    ),
    (
        "Does Polycade offer financing?",
        'https://polycade.com/pages/helphq-2#/collection/2971/article/11888"',
    ),
    (
        "Do you have a coin-op option to charge for play?",
        'https://polycade.com/pages/helphq-2#/collection/2971/article/11889"',
    ),
    (
        "Can I try a Polycade before I purchase one?",
        'https://polycade.com/pages/helphq-2#/collection/2971/article/11890"',
    ),
    (
        "How much does the Polycade cost?",
        'https://polycade.com/pages/helphq-2#/collection/2971/article/11891"',
    ),
    (
        "Compatible Xbox Controllers",
        'https://polycade.com/pages/helphq-2#/collection/2971/article/12402"',
    ),
    (
        "How to link your Polycade Limiteds and Polycade AGS accounts",
        'https://polycade.com/pages/helphq-2#/collection/2971/article/23839"',
    ),
    (
        "Disable QA Software",
        'https://polycade.com/pages/helphq-2#/collection/2971/article/28953"',
    ),
    (
        "What is Polycade AGS",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/11893"',
    ),
    (
        "Polycade AGS Installation",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/11894"',
    ),
    (
        "Making AGS your default interface",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/11895"',
    ),
    (
        "Updating Steam Settings",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/11896"',
    ),
    (
        "Adding ROMs",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/11897"',
    ),
    (
        "Adding custom images for games",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/11898"',
    ),
    (
        "Adding games from Steam",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/11899"',
    ),
    (
        "Removing games from Polycade AGS",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/11900"',
    ),
    (
        "What kind of internet support is required?",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/11901"',
    ),
    (
        "Adding games from GOG",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/11902"',
    ),
    (
        "Purchasing games from Polycade AGS Store",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/12385"',
    ),
    (
        "How do I create a Polycade account?",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/12650"',
    ),
    (
        "Redeeming Gift Cards or Store Credit",
        'https://polycade.com/pages/helphq-2#/collection/2972/article/19223"',
    ),
    (
        "Supported Platforms",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/11904"',
    ),
    (
        "What are ROMs?",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/11905"',
    ),
    (
        "What's an Emulator?",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/11906"',
    ),
    (
        "Can I play any game I want?",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/11909"',
    ),
    (
        "Does Polycade just play old games?",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/11910"',
    ),
    (
        "Adding games",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/11911"',
    ),
    (
        "How many games can it hold?",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/11912"',
    ),
    (
        "Should I get antivirus software?",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/11913"',
    ),
    (
        "Compatible Steam Games",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/12403"',
    ),
    (
        "Adding Additional Emulators",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/26344"',
    ),
    (
        "Removing games",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/28144"',
    ),
    (
        "Arcade (MAME) ROM errors",
        'https://polycade.com/pages/helphq-2#/collection/2973/article/28952"',
    ),
    (
        "Steam Tab Issue",
        'https://polycade.com/pages/helphq-2#/collection/2974/article/11918"',
    ),
    (
        "Steam stuck on blue screen",
        'https://polycade.com/pages/helphq-2#/collection/2974/article/11919"',
    ),
    (
        "Redeeming Steam Keys",
        'https://polycade.com/pages/helphq-2#/collection/2974/article/11920"',
    ),
    (
        "How to fullscreen a game",
        'https://polycade.com/pages/helphq-2#/collection/2974/article/11921"',
    ),
    (
        "How do I find games on Steam that will work best on Polycade?",
        'https://polycade.com/pages/helphq-2#/collection/2974/article/11922"',
    ),
    (
        "Unable to log in, even with scroll function",
        'https://polycade.com/pages/helphq-2#/collection/2974/article/11923"',
    ),
    (
        "Game list won't scroll",
        'https://polycade.com/pages/helphq-2#/collection/2974/article/11924"',
    ),
    (
        "How to uninstall Steam games",
        'https://polycade.com/pages/helphq-2#/collection/2974/article/17465"',
    ),
    (
        "Testing joysticks &amp; buttons",
        'https://polycade.com/pages/helphq-2#/collection/2975/article/11925"',
    ),
    (
        "Controller not working",
        'https://polycade.com/pages/helphq-2#/collection/2975/article/11926"',
    ),
    (
        "What do all the buttons do?",
        'https://polycade.com/pages/helphq-2#/collection/2975/article/11927"',
    ),
    (
        "Keyboard shortcuts",
        'https://polycade.com/pages/helphq-2#/collection/2975/article/11928"',
    ),
    (
        "Gameplay controls",
        'https://polycade.com/pages/helphq-2#/collection/2975/article/11929"',
    ),
    (
        "How to pair your controller",
        'https://polycade.com/pages/helphq-2#/collection/2975/article/11930"',
    ),
    (
        "Recommended controllers",
        'https://polycade.com/pages/helphq-2#/collection/2975/article/11931"',
    ),
    (
        "How to Use a Wireless Xbox 360 Controller on a PC",
        'https://polycade.com/pages/helphq-2#/collection/2975/article/12401"',
    ),
    (
        "Using AGS without a Controller",
        'https://polycade.com/pages/helphq-2#/collection/2975/article/12437"',
    ),
    (
        'Removing the "Control Panel"',
        'https://polycade.com/pages/helphq-2#/collection/2975/article/13006"',
    ),
    (
        "Light Guns",
        'https://polycade.com/pages/helphq-2#/collection/2975/article/26345"',
    ),
    (
        "Mounting instructions",
        'https://polycade.com/pages/helphq-2#/collection/2976/article/11932"',
    ),
    (
        "What do I need to mount the Polycade?",
        'https://polycade.com/pages/helphq-2#/collection/2976/article/11933"',
    ),
    (
        "Does Polycade offer installation?",
        'https://polycade.com/pages/helphq-2#/collection/2976/article/11934"',
    ),
    (
        "Is there a way to use a Polycade without a wall?",
        'https://polycade.com/pages/helphq-2#/collection/2976/article/11935"',
    ),
    (
        "LED Backlights Setup",
        'https://polycade.com/pages/helphq-2#/collection/2976/article/28956"',
    ),
    (
        "Can I customize the look of my Polycade?",
        'https://polycade.com/pages/helphq-2#/collection/2979/article/11944"',
    ),
    (
        "Installing a dimmer",
        'https://polycade.com/pages/helphq-2#/collection/2979/article/11946"',
    ),
    (
        "Disabling Startup Programs",
        'https://polycade.com/pages/helphq-2#/collection/4100/article/12400"',
    ),
    (
        "Fully resetting and re-installing Windows",
        'https://polycade.com/pages/helphq-2#/collection/4100/article/18726"',
    ),
    (
        "How do I connect to Wi-Fi?",
        'https://polycade.com/pages/helphq-2#/collection/4100/article/19222"',
    ),
    (
        "New Polycade machine setup instructions",
        'https://polycade.com/pages/helphq-2#/collection/4100/article/20404"',
    ),
    (
        "Disable Windows Sign-in Button",
        'https://polycade.com/pages/helphq-2#/collection/4100/article/28959"',
    ),
    (
        "My sound isn't working",
        'https://polycade.com/pages/helphq-2#/collection/4548/article/17529"',
    ),
    (
        "Polycade Won't Power On",
        'https://polycade.com/pages/helphq-2#/collection/4548/article/21253"',
    ),
    (
        "Black screen after powering on",
        'https://polycade.com/pages/helphq-2#/collection/4548/article/21254"',
    ),
    (
        "How to open your Polycade",
        'https://polycade.com/pages/helphq-2#/collection/4548/article/21255"',
    ),
    (
        "Screen does not turn on",
        'https://polycade.com/pages/helphq-2#/collection/4548/article/21257"',
    ),
    (
        "Updating Controller Firmware",
        'https://polycade.com/pages/helphq-2#/collection/4548/article/27861"',
    ),
]
output = ingestor.parse_qna_subpages(temp)

outfile = open("qa_subpage_output.txt", "w")

for i in range(0, len(output)):
    outfile.write("-------------------------------\n")
    outfile.write(f"{i+1}. {output[i][0]}\n")
    outfile.write("-------------------------------\n")
    outfile.write(output[i][1])
outfile.close()
