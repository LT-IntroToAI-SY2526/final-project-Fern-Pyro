import re, string, calendar, requests, time
from wikipedia import WikipediaPage
import wikipedia
from bs4 import BeautifulSoup
from match import match
from typing import List, Callable, Tuple, Any, Match


def get_page_html(title: str) -> str:
    search_response = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={"action": "query", "list": "search", "srsearch": title, "format": "json"},
        headers={"User-Agent": "intro-ai-class/1.0"},
        timeout=10
    )
    results = search_response.json().get("query", {}).get("search", [])
    if results:
        title = results[0]["title"]  # use the top search result title
        print(f"Searching Wikipedia for: {title}")
    
    for attempt in range(5):
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "redirects": True,
            },
            headers={"User-Agent": "intro-ai-class/1.0"}
        )
        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 5))
            print(f"Rate limited — waiting {wait}s before retrying '{title}'...")
            time.sleep(wait)
            continue
        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if "error" not in data:
                time.sleep(2)  # polite delay after every successful call
                return data["parse"]["text"]["*"]
    raise ConnectionError(f"Could not retrieve Wikipedia page for '{title}' after 5 attempts")


def get_first_infobox_text(html: str) -> str:
    """Gets first infobox html from a Wikipedia page (summary box)

    Args:
        html - the full html of the page

    Returns:
        text of just the first infobox
    """
    soup = BeautifulSoup(html, "html.parser") #BeautfulSoup object
    results = soup.find_all(class_="infobox") #searching for a tag with the CSS class "infobox" 
#   html tags are used to mark the start of html elements
#     tags must be closed in the order they were opened:
#         ex. <strong><em>This is really important!</em></strong> 
#   html attributes contain additional information
#     ex. <img src="mydog.jpg" alt="A photo of my dog.">
#         - scr and alt are attributes of the <img> tag

    if not results:
        raise LookupError("Page has no infobox")
    return results[0].text

def get_relevant_section(html: str) -> str:
    """Extracts all readble text from Wikipedia page."""
    soup = BeautifulSoup(html, "html.parser")
    results = soup.find_all(id="Section_Title") #class_=mw-headline
    #print(soup)

    if not results:
        raise LookupError("Page has no such section") 
    return results.text

def extract_wikipedia_text(html: str) -> str:
    """Extracts all readable text from a Wikipedia page."""
    soup = BeautifulSoup(html, "html.parser")
    print(soup)
    # Main content container
    #content = soup.find_all(class_="mw-content-text")
    content = soup.find("div", id="mw-parser-output")
    #print(content)
    if content is None:
        raise LookupError("Could not find main content area")
    #return content.text
    # return content[0].text
    # Remove elements you probably don't want
    for tag in content.find_all(["table", "style", "script", "sup", "span"], recursive=True):
        tag.decompose()
    return content[0].text
    # # Extract clean text
    # text = content.get_text(separator="\n", strip=True)
    # return text

def get_lead_paragraphs(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", {"class": "mw-parser-output"})
    paragraphs = []

    for child in content.children:
        if child.name == "p":
            paragraphs.append(child.get_text(strip=True))
        elif child.name and child.name.startswith("h"):
            break

    return "\n\n".join(paragraphs)

def clean_text(text: str) -> str:
    """Cleans given text removing non-ASCII characters and duplicate spaces & newlines

    Args:
        text - text to clean

    Returns:
        cleaned text
    """
    only_ascii = "".join([char if char in string.printable else " " for char in text])
    no_dup_spaces = re.sub(" +", " ", only_ascii)
    no_dup_newlines = re.sub("\n+", "\n", no_dup_spaces)
    return no_dup_newlines


def get_match(
    text: str,
    pattern: str,
    error_text: str = "Page doesn't appear to have the property you're expecting",
) -> Match:
    """Finds regex matches for a pattern

    Args:
        text - text to search within
        pattern - pattern to attempt to find within text
        error_text - text to display if pattern fails to match

    Returns:
        text that matches
    """
    p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    match = p.search(text)

    if not match:
        raise AttributeError(error_text)
    return match

def get_pop_dens(name: str) -> str:
    """Gets birth date of the given person

    Args:
        name - name of country

    Returns:
        population density for given country
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    # infobox_text = clean_text(extract_wikipedia_text(get_page_html(name)))
    # infobox_text = clean_text(get_lead_paragraphs(get_page_html(name)))
    print(f"{infobox_text}")
    pattern = r"(?:Density)(?P<pop_dens>.+/km2)"
    error_text = (
        "Page infobox has no population density information"
    )
    match = get_match(infobox_text, pattern, error_text)

    return match.group("pop_dens")


def get_gdp_per_capita(name: str) -> str:
    """Gets birth date of the given person

    Args:
        name - name of country

    Returns:
        real gdp per capita for given country
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    print(f"{infobox_text}")
    pattern = r"(?:Per capita)(?P<gdp> .\d+,\d+|.\d+)"
    error_text = (
        "Page infobox has no gdp per capita information"
    )
    match = get_match(infobox_text, pattern, error_text)

    return match.group("gdp")

def get_nru(name: str) -> str:
    """Gets birth date of the given person

    Args:
        name - name of country

    Returns:
        real gdp per capita for given country
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    print(f"{infobox_text}")
    pattern = r"(?:Per capita)(?P<gdp> .\d+,\d+|.\d+)"
    error_text = (
        "Page infobox has no natural rate of unemploymnet information"
    )
    match = get_match(infobox_text, pattern, error_text)

    return match.group("gdp")

#below are action functions

def pop_density(matches: List[str]) -> List[str]:
    """Returns birth date of named person in matches

    Args:
        matches - match from pattern of country's name to find population density of

    Returns:
        population density of given country
    """
    return [get_pop_dens(matches[0])]

def gdp_per_capita(matches: List[str]) -> List[str]:
    """Returns birth date of named person in matches

    Args:
        matches - match from pattern of country's name to find gdp per capita of

    Returns:
        gdp per capita of given country
    """
    return [get_gdp_per_capita(matches[0])]

def nru(matches: List[str]) -> List[str]:
    """Returns birth date of named person in matches

    Args:
        matches - match from pattern of country's name to find natural rate of unemployment of

    Returns:
        NRU of given country
    """
    return [get_nru(matches[0])]

# dummy argument is ignored and doesn't matter
def bye_action(dummy: List[str]) -> None:
    raise KeyboardInterrupt

# type aliases to make pa_list type more readable, could also have written:
# pa_list: List[Tuple[List[str], Callable[[List[str]], List[Any]]]] = [...]
Pattern = List[str]
Action = Callable[[List[str]], List[Any]]

# The pattern-action list for the natural language query system. It must be declared
# here, after all of the function definitions
pa_list: List[Tuple[Pattern, Action]] = [
    ("what is the population density of %".split(), pop_density),
    ("what is % gdp per capita".split(), gdp_per_capita),
    ("what is the natural unemployment rate of %".split(), nru),
    (["bye"], bye_action),
]


def search_pa_list(src: List[str]) -> List[str]:
    """Takes source, finds matching pattern and calls corresponding action. If it finds
    a match but has no answers it returns ["No answers"]. If it finds no match it
    returns ["I don't understand"].

    Args:
        source - a phrase represented as a list of words (strings)

    Returns:
        a list of answers Will be ["I don't understand"] if it finds no matches and
        ["No answers"] if it finds a match but no answers
    """
    for pat, act in pa_list:
        mat = match(pat, src)
        if mat is not None:
            answer = act(mat)
            return answer if answer else ["No answers"]

    return ["I don't understand"]


def query_loop() -> None:
    """The simple query loop. The try/except structure is to catch Ctrl-C or Ctrl-D
    characters and exit gracefully"""
    print("Welcome to the wikipedia chatbot!\n")
    while True:
        try:
            print()
            query = input("Your query? ").replace("?", "").lower().split()
            answers = search_pa_list(query)
            for ans in answers:
                print(ans)

        except (KeyboardInterrupt, EOFError):
            break

    print("\nSo long!\n")

query_loop()