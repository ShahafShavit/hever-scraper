import os
import sqlite3
from sqlite3 import Error
import time
import random
from bs4 import BeautifulSoup
from timeit import default_timer as timer
import datetime
import atexit
import re
from openai import OpenAI
import requests
from ast import literal_eval

categories = {
    "מזון ומשקאות": ["מסעדות", "סופרמרקטים", "בתי קפה", "מאפיות"],
    "הלבשה": ["בגדי גברים", "בגדי נשים", "בגדי ילדים", "אביזרים", "ביגוד לכל המשפחה", "ביגוד ספורט", "הנעלה",
              "תכשיטים"],
    "אלקטרוניקה": ["מחשבים", "טלפונים ניידים", "מכשירי חשמל ביתיים", "אביזרי אלקטרוניקה"],
    "בריאות ויופי": ["קוסמטיקה", "מכוני כושר", "בתי מרקחת", "קליניקות, מרכזי רפואה ובריאות", "ספא", "ראייה ומשקפיים"],
    "פנאי ובידור": ["בתי קולנוע", "פארקים", "הופעות חיות", "מוזיאונים", "סוחר כרטיסים", "משחקיות ופעילויות לילדים"],
    "תחבורה": ["תחבורה ציבורית", "אופניים וקטנועים וקלנועיות", "חניונים"],
    "סלולר": ["מכשירים סלולארים", "חבילות סלולאר וגלישה"],
    "דיור ונדל\"ן": ["נדל\"ן", "שירותי תחזוקה", ],
    "חינוך": ["בתי ספר", "קורסים וסדנאות", "אוניברסיטאות", "ספריות"],
    "שירותים פיננסיים": ["בנקים", "ביטוחים", "הלוואות", "ייעוץ פיננסי"],
    "טכנולוגיה": ["פיתוח תוכנה", "שירותי אינטרנט", "מערכות מידע", "שירותי IT", "מוצרי מולטימדיה"],
    "מסחר קמעונאי": ["חנויות כלבו", "חנויות מתנות וצעצועים", "חנויות ספרים", "חנויות נוחות", "רהיטים לבית ולגינה",
                     "חנויות פרחים", "ציוד משרדי", "ציוד צילום ופיתוח תמונות", "נשק ואבטחה אישית",
                     "ציוד מחנאות וטיולים", "ציוד ומזון לבעלי חיים", "כלי מטבח", "ציוד ספורט ואקסטרים", "גלריות ואמנות",
                     "בדים וטקסטיל", "ציוד לגיל הרך"],
    "מסחר סיטונאי": ["ציוד מקצועי", "מוצרי בניין", "מוצרי תעשייה", "סחורות כלליות", "ציוד גינון וחקלאות"],
    "רכב": ["מכירת רכבים", "מוסכים", "אביזרי רכב", "השכרת רכב"],
    "תיירות": ["מלונות", "סוכנויות נסיעות", "אטרקציות תיירותיות", "שירותי תיירות", "מועדון נופש"],
    "פרסום ושיווק": ["לוח מודעות", "חברות פרסום", "חברות שיווק", "עיתונים ומגזינים"],
    "כללי": ["אבל ומצבות", "לא מוגדר", "אירועים וחתונות", "שליחויות, ייבוא וייצוא", "הפקות אירועים"]
}


def cut_long_prompt(prompt, by: int = 0):
    try:
        if by == 0:
            return prompt
        return prompt[:by]
    except Exception:
        return prompt


def convert_categories_to_string(categories):
    category_mapping = {
        "מזון ומשקאות": "Food and Beverages",
        "הלבשה": "Clothing",
        "אלקטרוניקה": "Electronics",
        "בריאות ויופי": "Health and Beauty",
        "פנאי ובידור": "Leisure and Entertainment",
        "תחבורה": "Transportation",
        "דיור ונדל\"ן": "Housing and Real Estate",
        "חינוך": "Education",
        "שירותים פיננסיים": "Financial Services",
        "טכנולוגיה": "Technology",
        "מסחר קמעונאי": "Retail",
        "מסחר סיטונאי": "Wholesale",
        "רכב": "Automotive",
        "תיירות": "Tourism",
        "פרסום ושיווק": "Advertising and Marketing",
        "כללי": "General"
    }

    subcategory_mapping = {
        "מסעדות": "Restaurants",
        "סופרמרקטים": "Supermarkets",
        "בתי קפה": "Cafés",
        "מאפיות": "Bakeries",
        "בגדי גברים": "Men's Clothing",
        "בגדי נשים": "Women's Clothing",
        "בגדי ילדים": "Children's Clothing",
        "אביזרים": "Accessories",
        "ביגוד לכל המשפחה": "General Clothing",
        "ביגוד ספורט": "Sports Apparel",
        "מחשבים": "Computers",
        "טלפונים ניידים": "Mobile Phones",
        "מכשירי חשמל ביתיים": "Home Appliances",
        "אביזרי אלקטרוניקה": "Electronic Accessories",
        "קוסמטיקה": "Cosmetics",
        "מכוני כושר": "Gyms",
        "בתי מרקחת": "Pharmacies",
        "קליניקות": "Clinics",
        "ספא": "Spa",
        "בתי קולנוע": "Cinemas",
        "פארקים": "Parks",
        "הופעות חיות": "Live Shows",
        "מוזיאונים": "Museums",
        "סוחר כרטיסים": "Ticket Retailer",
        "תחבורה ציבורית": "Public Transportation",
        "אופניים וקטנועים": "Bicycles and Scooters",
        "חניונים": "Parking",
        "נדל\"ן": "Real Estate",
        "שירותי תחזוקה": "Maintenance Services",
        "רהיטים": "Furniture",
        "ציוד לבית": "Home Equipment",
        "בתי ספר": "Schools",
        "קורסים פרטיים": "Private Courses",
        "אוניברסיטאות": "Universities",
        "ספריות": "Libraries",
        "בנקים": "Banks",
        "ביטוחים": "Insurances",
        "הלוואות": "Loans",
        "ייעוץ פיננסי": "Financial Consulting",
        "פיתוח תוכנה": "Software Development",
        "שירותי אינטרנט": "Internet Services",
        "מערכות מידע": "Information Systems",
        "שירותי IT": "IT Services",
        "חנויות כלבו": "Department Stores",
        "חנויות מתנות": "Gift Shops",
        "חנויות ספרים": "Bookstores",
        "חנויות נוחות": "Convenience Stores",
        "רהיטים לבית ולגינה": "Indoor & Outdoor Decor",
        "חנויות פרחים": "Flower Shops",
        "ציוד מקצועי": "Professional Equipment",
        "מוצרי בניין": "Building Materials",
        "מוצרי תעשייה": "Industrial Products",
        "סחורות כלליות": "General Goods",
        "ציוד גינון וחקלאות": "Gardening & Farming supplies",
        "מכירת רכבים": "Car Sales",
        "מוסכים": "Garages",
        "אביזרי רכב": "Car Accessories",
        "השכרת רכב": "Car Rental",
        "מלונות": "Hotels",
        "סוכנויות נסיעות": "Travel Agencies",
        "אטרקציות תיירותיות": "Tourist Attractions",
        "שירותי תיירות": "Tourism Services",
        "מועדון נופש": "Resort Club",
        "לוח מודעות": "Bulletin Board",
        "חברות פרסום": "Advertising Companies",
        "חברות שיווק": "Marketing Companies",
        "אבל ומצבות": "Grief and Tombstones",
        "לא מוגדר": "Undefined"
    }

    result = ""
    for i, (category, subcategories) in enumerate(categories.items(), start=1):
        category_name = category_mapping.get(category, category)
        result += f"{i}. {category} ({category_name})\n"
        for subcategory in subcategories:
            subcategory_name = subcategory_mapping.get(subcategory, subcategory)
            result += f"   - {subcategory} ({subcategory_name})\n"
        result += "\n"
    return result.strip()


def API_CALL(client, store_desc: str, trunc_desc_to: int, options: int = 1) -> tuple:
    """
    :param client: OPENAI client
    :param store_desc: a string description of the store
    :return: a tuple with ((Main_category, sub-category), tokenUsageStats
    """
    main_prompt = """You are a worker of mine, analyzing the main category and sub-category of a given store by a given short text description. 
    You will classify it into one of the given main categories and each main category will have a few sub-categories. 
    Respond very simply with a '("main category", "sub category", confidence_level)' tuple-like response, with quotation marks around the categories. Use the provided Hebrew categories and sub-categories.
    confidence_level is a measurement for you to specify how confident you are with the categorization, it's a scale of 1-100.
    confidence_level must portray an accurate representation of your confidence level. it is ok for it to be anywhere on the scale.
    I dont want to see false confidence.
    ALWAYS RESPOND IN HEBREW, ALWAYS USE THE CATEGORY NAME AND NOT NUMERICAL IDENTIFIER.
    ALWAYS CHOOSE FROM CATEGORIES BELOW, DONT GENERATE CATEGORIES BY YOURSELF. IF YOU ARE UNSURE, LOWER THE CONFIDENCE LEVEL BELOW 50.
    PLEASE ALWAYS GIVE THREE DIFFERENT OPTIONS, ORDERED FROM MOST CONFIDENCE TO LEAST: 
    ((main_1, sub_category, confidence), (main_2, sub_category2, confidence), (main_3, sub_category3, confidence))

    Main Categories and Sub-Categories as a dictionary:
    """ + str(categories) + """
    Please analyze the following store description and categorize it accordingly:
    """

    """    1. מזון ומשקאות (Food and Beverages)
       - מסעדות (Restaurants)
       - סופרמרקטים (Supermarkets)
       - בתי קפה (Cafés)
       - מאפיות (Bakeries)

    2. הלבשה (Clothing)
       - בגדי גברים (Men's Clothing)
       - בגדי נשים (Women's Clothing)
       - בגדי ילדים (Children's Clothing)
       - אביזרים (Accessories)
       - ביגוד לכל המשפחה (General Clothing)
       - ביגוד ספורט (Sports Apparel)

    3. אלקטרוניקה (Electronics)
       - מחשבים (Computers)
       - טלפונים ניידים (Mobile Phones)
       - מכשירי חשמל ביתיים (Home Appliances)
       - אביזרי אלקטרוניקה (Electronic Accessories)

    4. בריאות ויופי (Health and Beauty)
       - קוסמטיקה (Cosmetics)
       - מכוני כושר (Gyms)
       - בתי מרקחת (Pharmacies)
       - קליניקות (Clinics)
       - ספא (Spa)

    5. פנאי ובידור (Leisure and Entertainment)
       - בתי קולנוע (Cinemas)
       - פארקים (Parks)
       - הופעות חיות (Live Shows)
       - מוזיאונים (Museums)
       - סוחר כרטיסים (Ticket Retailer)

    6. תחבורה (Transportation)
       - תחבורה ציבורית (Public Transportation)
       - אופניים וקטנועים (Bicycles and Scooters)
       - חניונים (Parking)

    7. דיור ונדל"ן (Housing and Real Estate)
       - נדל"ן (Real Estate)
       - שירותי תחזוקה (Maintenance Services)
       - רהיטים (Furniture)
       - ציוד לבית (Home Equipment)

    8. חינוך (Education)
       - בתי ספר (Schools)
       - קורסים פרטיים (Private Courses)
       - אוניברסיטאות (Universities)
       - ספריות (Libraries)

    9. שירותים פיננסיים (Financial Services)
       - בנקים (Banks)
       - ביטוחים (Insurances)
       - הלוואות (Loans)
       - ייעוץ פיננסי (Financial Consulting)

    10. טכנולוגיה (Technology)
        - פיתוח תוכנה (Software Development)
        - שירותי אינטרנט (Internet Services)
        - מערכות מידע (Information Systems)
        - שירותי IT (IT Services)

    11. מסחר קמעונאי (Retail)
        - חנויות כלבו (Department Stores)
        - חנויות מתנות (Gift Shops)
        - חנויות ספרים (Bookstores)
        - חנויות נוחות (Convenience Stores)
        - רהיטים לבית ולגינה (Indoor & Outdoor Decor)
        - חנויות פרחים (Flower Shops)

    12. מסחר סיטונאי (Wholesale)
        - ציוד מקצועי (Professional Equipment)
        - מוצרי בניין (Building Materials)
        - מוצרי תעשייה (Industrial Products)
        - סחורות כלליות (General Goods)
        - ציוד גינון וחקלאות (Gardening & Farming supplies)

    13. רכב (Automotive)
        - מכירת רכבים (Car Sales)
        - מוסכים (Garages)
        - אביזרי רכב (Car Accessories)
        - השכרת רכב (Car Rental)

    14. תיירות (Tourism)
        - מלונות (Hotels)
        - סוכנויות נסיעות (Travel Agencies)
        - אטרקציות תיירותיות (Tourist Attractions)
        - שירותי תיירות (Tourism Services)
        - מועדון נופש 

    15. פרסום ושיווק
        - לוח מודעות
        - חברות פרסום
        - חברות שיווק
    16. כללי
        - אבל ומצבות
        - לא מוגדר"""
    # print(convert_categories_to_string(categories))
    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4o",
        messages=[
            {"role": "system", "content": main_prompt},
            {"role": "user", "content": cut_long_prompt(store_desc, trunc_desc_to)}
        ]
    )

    return completion.choices[0].message.content, completion.usage


# Returns HTML Response string or None if page fetching failed
def fetch_page(url, cookies = None, headers= None) -> str or None:
    max_retries = 5
    delay = 1  # Initial delay in seconds

    with requests.Session() as session:
        # session.cookies.update(cookies)
        session.headers.update(headers)

        for attempt in range(max_retries):
            try:
                response = session.get(url)
            except requests.exceptions.ConnectTimeout:
                print("Connection Timeout.")
                return None
            if response.status_code == 200:
                # print("Successfully fetched the page!")
                # Ensure the response is correctly interpreted as UTF-8
                response.encoding = 'utf-8'
                return response.text
            elif response.status_code == 429:
                print(f"Rate limited. Retrying in {delay} seconds...")
                time.sleep(delay + random.uniform(0, 2))  # Add random delay
                delay *= 2  # Exponential backoff
            else:
                print(f"Failed to fetch the page. Status code: {response.status_code}")
                return None

    print("Failed to fetch the page after multiple attempts.")
    return None


# Returns a tuple with all the relevant data in the page
def parse_html_with_desc(html_content) -> tuple:
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the title inside <p class="h3">
    title_element = soup.find('p', class_='h3')
    title = title_element.get_text(strip=True) if title_element else None
    if title == "": title = None
    # Find the percentage inside <span>
    percentage_element = soup.find('span', string=lambda text: text and '%' in text)
    percentage = percentage_element.get_text(strip=True) if percentage_element else None

    # Find the link inside <span>
    link_element = soup.find('span', dir='ltr')
    link = link_element.get_text(strip=True) if link_element else None
    if link == "": link = None

    # Find the description inside the <div> tag
    description_div = soup.find_all('p')
    description = description_div[2].get_text(strip=True) if description_div else None
    description = description.replace('\n', ' ')

    # Find the image URL inside <img>
    image_element = soup.find('img', class_='img-fluid bg-white border rounded-lg p-3')
    image_url = image_element['src'] if image_element else None
    if not title:
        image_url = None
    return title, percentage, link, description, image_url


# Returns Sqlite Connection object if successful. otherwise returns None.
def create_connection(db_file: str) -> sqlite3.Connection or None:
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"SQLite Database connected: {db_file}")
    except Error as e:
        print(f"Error: {e}")
    return conn


# Creates table if not exists, Returns None
def create_table(conn: sqlite3.Connection) -> None:
    create_table_sql = """
    CREATE TABLE scraped_data (
        id INTEGER PRIMARY KEY,
        store_id INTEGER NOT NULL UNIQUE,
        title TEXT,
        discount REAL,
        is_fixed INTEGER,
        link TEXT,
        url TEXT,
        description TEXT,
        image_url TEXT,
        last_scrape TIMESTAMP,
        last_modification TIMESTAMP,
        main_category TEXT,
        sub_category TEXT,
        outputTokens INT,
        inputTokens INT,
        totalTokens INT
        );
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        print("Table created successfully.")
    except Error as e:
        print(f"Error: {e}")


# Creates tables and sets field types if not exists. Returns Sqlite3 Connection object.
def initialize_database(db_file: str) -> sqlite3.Connection or None:
    conn = create_connection(db_file)
    if conn is not None:
        create_table(conn)
    return conn


# Inserts new data into the database. returns the rowIndex integer it inserted to.
def insert_data(conn: sqlite3.Connection, data: tuple or list) -> int or None:
    sql = '''
    INSERT INTO scraped_data(store_id, title, discount, is_fixed, link, url, description, image_url, last_scrape, last_modification)
    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    cur = conn.cursor()
    cur.execute(sql, data)
    conn.commit()
    return cur.lastrowid


# Updates a record in the database. returns None.
def update_data(conn: sqlite3.Connection, data: tuple or list) -> None:
    sql = '''
    UPDATE scraped_data
    SET title = ?,
        discount = ?,
        is_fixed = ?,
        link = ?,
        url = ?,
        description = ?,
        image_url = ?,
        last_scrape = ?,
        last_modification = ?
    WHERE store_id = ?
    '''
    cur = conn.cursor()
    cur.execute(sql, data)
    conn.commit()


# Update a record's last-scrape date-time. returns None
def update_last_scrape(conn: sqlite3.Connection, store_id: int or str, last_scrape: datetime.datetime) -> None:
    sql = '''
    UPDATE scraped_data
    SET last_scrape = ?
    WHERE store_id = ?
    '''
    cur = conn.cursor()
    cur.execute(sql, (last_scrape, store_id))
    conn.commit()


# Check if a record exists in a database, if so- returns row. Otherwise, returns None.
def check_if_exists(conn: sqlite3.Connection, store_id: int or str) -> list or None:
    sql = 'SELECT * FROM scraped_data WHERE store_id=?'
    cur = conn.cursor()
    cur.execute(sql, (store_id,))
    row = cur.fetchone()
    return row


# Returns all existing IDs currently in database
def get_existing_ids(conn: sqlite3.Connection) -> set:
    cur = conn.cursor()
    cur.execute("SELECT store_id FROM scraped_data")
    rows = cur.fetchall()
    return set([str(row[0]) for row in rows])


# Converts Human-form discount string to (float, fixed/non-fixed) tuple
def convert_discount(discount: str) -> tuple:
    try:
        value = float(discount.rstrip('%')) / 100.0
        is_fixed = True
    except ValueError:
        stripped_value = re.sub(r'[^\d]', '', discount)
        is_fixed = False
        value = float(stripped_value) / 100.0
        print(f"Non-fixed discount found: Original value: {discount} -> {value}")
    return value, is_fixed


# Takes seconds as float and converts it to HH:mm:ss.mm
def convert_duration(seconds: float) -> str:
    try:
        return f"{str(datetime.timedelta(seconds=seconds)).split('.')[0]}.{str(datetime.timedelta(seconds=seconds)).split('.')[1][:2]} (HH:mm:ss)"
    except IndexError:
        return f"{str(datetime.timedelta(seconds=seconds)).split('.')[0]} (HH:mm:ss)"


# Takes image url and filename (grabs the extension from the original file) and downloads it.
def download_image(image_url: str, new_name: str) -> None:
    with requests.Session() as session:
        # session.cookies.update(cookies)
        session.headers.update(headers)
        response = session.get(image_url)
        if response.status_code == 200:
            # Extract the file extension from the image URL
            file_extension = os.path.splitext(image_url)[-1]
            if not file_extension:
                file_extension = '.jpg'  # Default to .jpg if no extension found
            new_name_with_extension = new_name + file_extension
            os.makedirs("img\\", exist_ok=True)
            with open(new_name_with_extension, 'wb') as f:
                f.write(response.content)
            print(f"Image downloaded and saved as {new_name_with_extension}")
        else:
            print(f"Failed to download image from {image_url} | error code {response.status_code}")


def scrape_ids(conn: sqlite3.Connection, ids_range: range, check_alive_list: bool = False,
               check_dead_list: bool = False):
    """
    :param conn: database connection object
    :param ids_range: range of ids to scan
    :param check_alive_list: force re-check alive ids
    :param check_dead_list: force re-check dead-ids
    :return: None
    """
    url = "https://www.mcc.co.il/site/pg/st_reshet_out&p1="
    range_min, range_max = min(ids_range), max(ids_range)
    sleep_time = 3
    rand_min = 0.9
    rand_max = 1.8
    start_time = timer()
    counters = {'new_dead': 0, 'new_alive': 0, 'known_dead': 0, 'known_alive': 0, 'updated_dead': 0, 'updated_alive': 0}

    existing_ids_set = get_existing_ids(conn)

    ids_range = list(ids_range)
    for i in range(len(ids_range) - 1, -1, -1):
        if str(ids_range[i]) in existing_ids_set:
            if check_alive_list or check_dead_list:
                print(f"ID {ids_range[i]} found in existing list. Requested to be re-checked.")
            else:
                print(f"ID {ids_range[i]} found in existing list. Removing from search.")
                ids_range.pop(i)

    counter = 0
    # SCRAPE START
    print(f"Starting scraping process for IDs: ({range_min}-{range_max}), checking {len(ids_range)} IDs.")
    for i in ids_range:
        updated_url = url + str(i)
        html_content = fetch_page(updated_url, headers)
        if html_content:
            title, percentage, link, description, image_url = parse_html_with_desc(html_content)
            counter += 1
            last_scrape = datetime.datetime.now()
            if title and percentage:
                print(f"Found store ID {i} -> Name: {title} | Link: {updated_url}")
                discount, is_fixed = convert_discount(percentage)
                data = (
                    title, discount, is_fixed, link, updated_url, description, image_url, last_scrape, last_scrape, i)
                existing_record = check_if_exists(conn, i)
                if image_url:
                    download_image(image_url, f"img\\image_{i}")
                if existing_record:
                    if (
                            existing_record[2], existing_record[3], existing_record[4], existing_record[5],
                            existing_record[6],
                            existing_record[7], existing_record[8]) != (
                            title, discount, is_fixed, link, updated_url, description, image_url):
                        print(f"Updating existing ID {i} in the database.")
                        update_data(conn, data)
                        counters['updated_alive'] += 1
                    else:
                        print(f"No data change for ID {i}. Updating last_scrape only.")
                        update_last_scrape(conn, i, last_scrape)
                        counters['known_alive'] += 1
                else:
                    print(f"Inserting new ID {i} into the database.")
                    insert_data(conn, (
                        i, title, discount, is_fixed, link, updated_url, description, image_url, last_scrape,
                        last_scrape))
                    counters['new_alive'] += 1
            else:
                if check_if_exists(conn, i):
                    print(f"ID {i} exists in database but now marked as dead. Updating.")
                    update_data(conn, (None, None, None, None, None, None, None, last_scrape, last_scrape, i))
                    counters['updated_dead'] += 1
                else:
                    print(f"ID {i} not found in database. Adding as dead.")
                    insert_data(conn, (i, None, None, None, None, updated_url, None, None, last_scrape, last_scrape))
                    counters['new_dead'] += 1

        else:
            ans = input("Retry ID? (y/n)")
            if ans == 'y':
                i -= 1

        left_to_scrape = len(ids_range) - (counter + 1)
        min_time = convert_duration(sleep_time * rand_min * left_to_scrape)
        max_time = convert_duration(sleep_time * rand_max * left_to_scrape)
        avg_time = convert_duration(sleep_time * ((rand_min + rand_max) / 2) * left_to_scrape)
        current_sleeptime = sleep_time * random.uniform(rand_min, rand_max)
        print(
            f"({counter}/{len(ids_range)}) Finishing in: Min: {min_time} | Max: {max_time} | AVG: {avg_time}")
        print(f"AFM: halting for {current_sleeptime:.2f}s")
        time.sleep(current_sleeptime)

    end_time = timer()
    total_time = convert_duration(end_time - start_time)
    print(
        f"Finished checking {counter} webpages for stores, ranging ({range_min}-{range_max}) ids. This took {total_time}.")


def categorize_db(conn: sqlite3.Connection, openai_client, optimization: bool = False):
    cursor = conn.cursor()
    # Query rows where a certain column (e.g., 'store_description') is not null
    if optimization:
        cursor.execute(
            """SELECT id, description, title FROM scraped_data 
            WHERE description IS NOT NULL AND (confidence < 80 OR confidence IS NULL)""")
    else:
        cursor.execute(
            "SELECT id, description, title FROM scraped_data WHERE description IS NOT NULL AND confidence IS NULL")
    rows = cursor.fetchall()
    fetch_size = len(rows)
    current_row = 0
    for row in rows:
        current_row += 1
        row_id, store_description, title = row
        if len(str(store_description).strip()) == 0:
            with open("problem_ids.txt", 'a') as f:
                print(f"ERROR: {str(row_id)} -> No Description Available")
                f.write(f"ERROR: {str(row_id)} -> No Description Available")
            continue
        # Get the API response for the store description
        categories__, tokens = API_CALL(openai_client, f"{title}: {store_description}", 0)
        if optimization:
            try:
                output = literal_eval(categories__)
                good_options = []
                for option in output:
                    if option[0] in categories.keys():
                        if option[1] in categories[option[0]]:
                            good_options.append(option)
                cursor.execute(
                    "SELECT id, confidence, title, description, main_category, sub_category, link, url FROM "
                    "scraped_data WHERE id = ?", (row_id,))
                row = cursor.fetchone()
                print(f"Stores Left: {fetch_size - current_row}")
                print(f"ID | {row[0]} | Link: {row[6]} | Link: {row[7]}")
                print(f"Title: {row[2]}")
                print(f"תיאור: \n{row[3]}")
                found = False
                for option in good_options:
                    if option[2] >= 90:
                        found = True
                        choice = option
                    print(option)
                if not found:
                    try:
                        input_choice = int(input("Which one fits best? ")) - 1
                    except Exception:
                        break
                    if input_choice < len(good_options):
                        choice = good_options[input_choice]
                        cursor.execute(
                            "UPDATE scraped_data SET main_category = ?, sub_category = ?, confidence = ? WHERE id = ?",
                            (choice[0], choice[1], 91, row_id,))
                        conn.commit()
                    else:
                        continue
                else:
                    cursor.execute(
                        "UPDATE scraped_data SET main_category = ?, sub_category = ?, confidence = ? WHERE id = ?",
                        (choice[0], choice[1], 91, row_id,))
                    conn.commit()
            except SyntaxError:
                # print(f"*** --> ERROR WITH ID {row_id}")
                with open("problem_ids.txt", 'a') as f:
                    f.write(
                        f"ERROR: {str(row_id)} -> error parsing category return from OPENAI. RETURNED: ({categories__})")
                    print(
                        f"ERROR: {str(row_id)} -> error parsing category return from OPENAI. RETURNED: ({categories__})")
        else:
            try:
                good_categorization = False
                option1, option2, option3 = literal_eval(categories__)

                print(f"{row_id} -> {categories__}")
                if option1[0] in categories.keys():
                    if option1[1] in categories[option1[0]]:
                        good_categorization = True
                    else:
                        print("Wrong main-sub output")
            except SyntaxError:
                # print(f"*** --> ERROR WITH ID {row_id}")
                with open("problem_ids.txt", 'a') as f:
                    f.write(
                        f"ERROR: {str(row_id)} -> error parsing category return from OPENAI. RETURNED: ({categories__})")
                    print(
                        f"ERROR: {str(row_id)} -> error parsing category return from OPENAI. RETURNED: ({categories__})")
                continue

            if good_categorization:
                # continue
                # Update the database with the response
                cursor.execute("UPDATE scraped_data SET main_category = ?, sub_category = ?, outputTokens = ?, "
                               "inputTokens = ?, totalTokens = ?, confidence = ? WHERE id = ?",
                               (categories__[0], categories__[1],
                                tokens.completion_tokens,
                                tokens.prompt_tokens,
                                tokens.total_tokens, categories__[2],
                                row_id))
                conn.commit()


def cleanup():
    if conn:
        conn.close()
        print("SQLite connection is closed.")


def fix_confidence(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, confidence, title, description, main_category, sub_category, link, url FROM scraped_data WHERE confidence < 80")
    data = cursor.fetchall()
    for row in data:
        # print(row)
        print(f"confidence: {row[1]} | id {row[0]}")
        print(f"Link: {row[6]} | Link: {row[7]}")
        print(f"תיאור: {row[3]}")
        print(f"{row[4]} | {row[5]}")
        ans = input("OK?")
        if ans == "":
            cursor.execute("UPDATE scraped_data SET confidence = 90 where id = ?", (row[0],))
            conn.commit()


if __name__ == "__main__":
    atexit.register(cleanup)

    client = OpenAI()


    # Headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

    db_file = 'scraped_data.db'
    conn = initialize_database(db_file) # initialize database.
    scrape_ids(conn, range(0, 6000)) # First thing to do.
    #categorize_db(conn, client, optimization=False) # Second thing to do
    #categorize_db(conn, client, optimization=True) # Last thing to do
