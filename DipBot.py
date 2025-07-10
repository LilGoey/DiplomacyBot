from playwright.sync_api import sync_playwright
import re
import time
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
import os

load_dotenv()
api_key=os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

class DipBot():

    def __init__(self):
        self.current_season = ""
        self.current_phase = ""
        self.current_page = ""
        self.countryID = ""
        self.open_chats = []
        self.current_units = []
        self.opps = []
        self.possible_builds = {}
        self.number_of_builds = 0

        self.country_map = {
            0: "Global Chat",
            1: "Britain",
            2: "Egypt",
            3: "France",
            4: "Germany",
            5: "Italy",
            6: "Poland",
            7: "Russia",
            8: "Spain",
            9: "Turkey",
            10: "Ukraine"
        }

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

        self.model = genai.GenerativeModel("gemini-1.5-pro")
        self.chat = self.model.start_chat()

    def opening_prompt(self):

        country_name = self.country_map.get(int(str(self.countryID).strip()), f"Country {self.countryID}")

        prompt = f"""
        You are an expert strategist and swindler in the web game Diplomacy. 
        You will analyze and respond to player messages, come up with turn orders, and possibly even deceive other players. 
        You are working as an automated agent representing one country, and your job is to make tactical moves and act diplomatically in order to win the game.

        Game Overview:
        - There are 10 powers: Britain, France, Germany, Italy, Poland, Spain, Russia, Turkey, Ukraine, and Egypt (custom variant).
        - The game is turn-based. Each turn is either Spring or Autumn of a year (e.g., Spring 1995).
        - Players can message each other privately and propose alliances, betrayals, support, and moves.
        - You will be provided with: 
            - The current map as an image.
            - Recent chat logs from other players.
            - The current phase (either Diplomacy or Build)
            - List of current orders that need to be given

       You are a player in the game Diplomacy. You must follow the official rules of the game listed below. Do not explain your reasoning. Only use this information to:
        1. Formulate messages to other players.
        2. Decide what actions to take within the game.

        Rules of Diplomacy:

        The Goal:
        - Control 18 out of 34 supply centers to win.
        - Each supply center you control allows you to build one unit (army or fleet) at the end of the year.
        - If you lose a supply center, you must disband a unit.

        Units:
        - There are two unit types: Armies (land) and Fleets (coast/sea).
        - Armies cannot enter sea zones.
        - Fleets can convoy armies across sea zones using convoy orders.

        Orders:
        Each unit may be given one of the following orders per turn:
        - Hold: The unit stays in its territory and defends.
        - Move: The unit moves to an adjacent territory.
        - Support Move: The unit supports another unit's move into a specific territory.
        - Support Hold: The unit supports another unit to hold its position.
        - Convoy: Fleets can convoy armies across sea territories.

        Combat Rules:
        - All units are equal in strength.
        - An unsupported attack against a holding unit fails.
        - If two unsupported units move into the same territory, both fail (bounce).
        - To dislodge an occupied territory, the attacking unit must be supported.
        - Support is cut if the supporting unit is attacked, even if it is not dislodged.
        - A convoying fleet can be dislodged if it is attacked by a supported unit.
        - Convoying fleets can be supported to hold by adjacent fleets (not armies).

        Tactics Summary:
        - Bouncing: Two units moving into the same territory without support will both fail.
        - Support: Units can support other units to move or hold, increasing their effective strength.
        - Cutting Support: Attacking a supporting unit prevents it from providing support that turn.
        - Defensive Support Hold: A support hold can reinforce a unit to resist an otherwise successful attack.
        - Convoys: Fleets can chain convoy an army across multiple sea zones.

        You are expected to obey these rules exactly. When responding, never explain your decisions or describe your logic. Respond as a player taking actions or communicating with other players within the game.


        You are currently playing as the country {country_name}.

        
        """

        reply = self.chat.send_message(prompt)
        print(reply.text)

    def provide_chat_map_build(self, path):
        img = Image.open(path)
        country_name = self.country_map.get(int(str(self.countryID).strip()), f"Country {self.countryID}")
        
        prompt = f"""
        As a reminder you are playing as the country {country_name}

        It is currently the {bot.current_phase} in {bot.current_season}

        You will be creating units in order to assistwith your goal. You have to make a total of {bot.number_of_builds} new units. 
        You can build either an army or a fleet. Use these lists and the map to chose where the best teritory is to build a new unit and which.
        {bot.possible_builds}
        You cannot build two units on the same teritory so make sure your choices are different

        Your response should look exactly like this:
        confirmed_builds = (
            Build (your choice of Fleet/Army): "Country from possible builds list", 
            Build (your choice of Fleet/Army): "Country from possible builds list"
        )

        No additional explanation or information is needed, just the orders and make it a dictionary useable in python code.

        """

        reply = self.chat.send_message([prompt, img])
        print(reply.text)

    def provide_chat_map(self, path):
        img = Image.open(path)
        country_name = self.country_map.get(int(str(self.countryID).strip()), f"Country {self.countryID}")
        locations = [unit["location"] for unit in self.current_units]

        prompt = f"""
        You are playing as {country_name}

        Here is the current game map for {self.current_season} and it is the {self.current_phase} phase. 

        These are the units you have where they are currently stationed {locations}

        Using the given information I want you to provide me a list of orders as a python dictionary for example:
        orders: (
            fleet at Tunisia: Hold, 
            fleet at Persian Gulf: Move to Iran, 
            etc...
        )

        I also want a python dictionary in the same way but with any messages that you think might be necessary to send for example:
        messages: (
            Turkey: I am going to move my Persian fleet to Iran,
            Britian: Don't try to take Tunisia I am holding it...
        )

        No additional explanation or information is needed, just the orders and the messages.
        """

        reply = self.chat.send_message([prompt, img])

        print(reply.text)
        print("\n"+country_name)

        return reply.text
    
    def get_possible_builds(self):
        builds = [] 
        teritory_options = {}

        selector = (self.page.locator('select[ordertype="type"]')).nth(0)

        selector.select_option("Build Fleet")
        selections = (self.page.locator('select[ordertype="toTerrID"]')).nth(0)
        if selections:
            options = selections.locator('option')
            builds = options.all_inner_texts()
            builds = [b for b in builds if b.strip()]
            teritory_options["Build Fleet Options"] = builds

        selector.select_option("Build Army")
        selections = (self.page.locator('select[ordertype="toTerrID"]')).nth(0)
        if selections:
            options = selections.locator('option')
            builds = options.all_inner_texts()
            builds = [b for b in builds if b.strip()]
            teritory_options["Build Army Options"] = builds

        self.number_of_builds = self.page.locator('select[ordertype="type"]').count()

        self.possible_builds = teritory_options

    def login_fromlogin(self):
        LOGIN_URL = "https://www.vdiplomacy.com/logon.php"
        USERNAME = "MrChattyChat"
        PASSWORD = "100%Orange"

        # Go to the login page
        self.page.goto(LOGIN_URL)

        # Fill in login form
        self.page.fill('input[name="loginuser"]', USERNAME)
        self.page.fill('input[name="loginpass"]', PASSWORD)
        self.page.press('input[name="loginpass"]', 'Enter')

        # Wait for navigation
        self.page.wait_for_load_state("networkidle")
        print("Login successful. Current URL:", self.page.url)

        DipBot.current_page = self.page.url
    
    def goto_game_home(self):
        self.page.goto("https://www.vdiplomacy.com/board.php?gameID=63977#gamePanel")
        self.page.wait_for_load_state("networkidle")
        DipBot.current_page = self.page.url

    def get_current_gamePhase(self):
        phase = (self.page.locator("span.gamePhase").all_text_contents())[0]
        return phase

    def set_current_gamePhase(self):
        phase = self.get_current_gamePhase()
        self.current_phase = phase

    def get_current_gameDate(self):
        fulldate = (self.page.locator(".gameDate").all_text_contents())[0]
        
        return fulldate

    def set_current_gameDate(self):
        season = self.get_current_gameDate()
        self.current_season = season 
        
    def new_season_stage(self):
        current_season = self.get_current_gameDate()

        if current_season == self.current_season:
            return True
        else:
            return False

    def get_recent_chat_from_current(self):
        all_messages = self.page.locator('table.chatbox td.right')
        
        last_sent_index = -1
        
        for i in range(all_messages.count()):
            td = all_messages.nth(i)
            class_attr = td.get_attribute("class") or ""
            html = td.inner_html()

            if f"country{DipBot.countryID}" in class_attr and "messageFromMe" in html:
                last_sent_index = i

        if last_sent_index == -1:
            return all_messages.all_text_contents()
        

        recent = []
        for i in range(last_sent_index + 1, all_messages.count()):
            text = all_messages.nth(i).text_content()
            recent.append(text)
        
        return recent

    def goto_country_chat(self, countryID):

        if countryID in DipBot.open_chats:
            href = self.page.get_attribute(f"a.country{countryID}", 'href')
            href = (href.lstrip('.'))
        else:
            href = self.page.get_attribute(f"option.country{countryID}", 'value')
            href = "/" + href
        full_address = "https://www.vdiplomacy.com" + href
        self.page.goto(full_address)
        self.page.wait_for_load_state("networkidle")
        DipBot.current_page = self.page.url
    
    def get_countryIDs_from_open_chats(self):
        country_links = self.page.locator('#chatboxtabs a[class^="country"]')
        ids = []

        for i in range(country_links.count()):
            class_attr = country_links.nth(i).get_attribute("class")
            match = re.search(r'country(\d+)', class_attr)
            if match:
                cid = match.group(1)
                if cid == "0" or cid == self.countryID:
                    continue
                ids.append(cid)

        self.open_chats = ids

    def get_bot_countryID(self):
        country_span = self.page.locator('span.memberYourCountry').first
        class_attr = country_span.get_attribute("class")

        self.countryID = ((class_attr.split(" "))[0]).replace("country", "")

    def get_countryIDs_from_unread_msgs(self):
        country_ids = []
        unread_links = self.page.locator('#chatboxtabs a:has(img[alt="Unread message"])')
        for i in range(unread_links.count()):
            link = unread_links.nth(i)
            countryID = ((link.get_attribute('class')).lstrip("country")).replace(" ", "")
            country_ids.append(countryID)
        
        return country_ids

    def get_unit_ids_and_location(self):
        self.page.wait_for_selector('table.orders')
        rows = self.page.locator('table.orders tr')
        units = []

        for i in range(rows.count()):
            row = rows.nth(i)

            try:
                order_div = row.locator('td.order div')
                if not order_div.count():
                    continue

                unit_id = order_div.get_attribute('id')
                location_text = order_div.locator('span.orderBegin').inner_text().strip()
                if unit_id and location_text:    
                    units.append(
                        {
                            "id": unit_id,
                            "location": location_text
                        }
                    )

            except Exception as e:
                print("broken")
                continue

        self.current_units = units

    def start_functions(self):
        self.login_fromlogin()
        self.goto_game_home()
        self.get_bot_countryID()
        self.set_current_gameDate()
        self.set_current_gamePhase()
        self.get_countries_from_chatbox()
        self.opening_prompt()

    def click_on_builder(self):
        self.page.wait_for_selector('table.orders')
        rows = self.page.locator('table.orders tr')

        for i in range(rows.count()):
            row = rows.nth(i)
            orders = row.locator('select.orderDropDown')

            for j in range(orders.count()):
                order = orders.nth(j)
                order.click()

    def get_countries_from_chatbox(self):
        countries = [] 

        a_links = self.page.locator('#chatboxtabs a')
        for i in range(a_links.count()):
            a = a_links.nth(i)
            href = a.get_attribute('href')
            text = a.inner_text().strip()

            match = re.search(r'msgCountryID=(\d+)', href or "")
            if match and text.lower() != 'global':
                countries.append({
                    'name': text,
                    'id': match.group(1)
                })

        options = self.page.locator('#chatboxtabs select option')
        for i in range(options.count()):
            option = options.nth(i)
            value = option.get_attribute('value')
            name = option.inner_text().strip()

            match = re.search(r'msgCountryID=(\d+)', value or "")
            if match and name.lower() != 'open new chat:':
                countries.append({
                    'name': name,
                    'id': match.group(1)
                })

        for country in countries:
            if self.countryID in country.values():
                countries.remove(country)

        self.opps = countries        

    def is_ready(self):
        button_value = self.page.locator("input.form-submit.spaced-button")
        ready_or_not = button_value.get_attribute("value")

        if ready_or_not == "Ready":
            ready = False
        else:
            ready = True
        
        return ready

    def save_map_screenshot_with_turn_number(self):
        map_element = self.page.locator("#mapImage")
        src = map_element.get_attribute("src")

        # Extract the turn number before '-small.map'
        match = re.search(r'/(\d+)-small\.map', src)
        turn_number = match.group(1) if match else "unknown"

        self.page.wait_for_selector("#mapImage", state="visible", timeout=5000)
        filename = f"./map_turn_{turn_number}.png"
        map_element.screenshot(path=filename)

        return filename

    def get_orders(self):
        orders = []

        # Locate all rows in the orders table
        rows = self.page.locator('table.orders tbody tr')

        for i in range(rows.count()):
            row = rows.nth(i)

            # Get unit type: "Army" or "Fleet"
            unit_icon = row.locator('td.uniticon img')
            unit_type = unit_icon.get_attribute('alt').strip()

            # Get order container
            order_div = row.locator('td.order div')

            # Extract current territory (e.g., "The fleet at Algeria" → "Algeria")
            order_text = order_div.locator('.orderSegment.orderBegin').inner_text().strip()
            if " at " in order_text:
                current_territory = order_text.split(" at ")[1].strip(" .")
            else:
                current_territory = None

            # Get the action dropdown
            action_select = order_div.locator('select[ordertype="type"]')
            selected_action = action_select.locator('option[selected]').get_attribute('value')
            possible_actions = action_select.locator('option').all_inner_texts()

            # Default values for movement options
            to_territory = None
            from_territory = None
            to_options = []
            from_options = []

            # Try to get destination options (toTerrID)
            to_selector = order_div.locator('select[ordertype="toTerrID"]')
            if to_selector.count() > 0:
                selected_to = to_selector.locator('option[selected]')
                to_territory = selected_to.inner_text().strip() if selected_to.count() > 0 else None
                to_options = [opt.strip() for opt in to_selector.locator('option').all_inner_texts() if opt.strip()]

            # Try to get source options (fromTerrID) for support move etc.
            from_selector = order_div.locator('select[ordertype="fromTerrID"]')
            if from_selector.count() > 0:
                selected_from = from_selector.locator('option[selected]')
                from_territory = selected_from.inner_text().strip() if selected_from.count() > 0 else None
                from_options = [opt.strip() for opt in from_selector.locator('option').all_inner_texts() if opt.strip()]

            orders.append({
                "unit_type": unit_type,
                "current_territory": current_territory,
                "selected_action": selected_action,
                "possible_actions": possible_actions,
                "to_territory": to_territory,
                "from_territory": from_territory,
                "to_options": to_options,
                "from_options": from_options
            })

        return orders


    def close(self):
        self.browser.close()
        self.playwright.stop()

if __name__ == "__main__":
    # On startup initialize the bot
    bot = DipBot()

    # Run through all the functions needed to start
    bot.start_functions()

    # Maybe have a function that will send out chats to all players once as the game starts
    # ???

    # Create the loop for the main game that will not end until the game reaches the 'finished' state
    while bot.current_phase != "Finished":      
        
        # will get all of the countryIDs from chats that are already open
        bot.get_countryIDs_from_open_chats()
        orders = bot.get_orders()
        print(orders)

        if not bot.is_ready():

            # get a screenshot of the current map saved along with it's filename
            filename = bot.save_map_screenshot_with_turn_number()
            #bot.provide_chat_map(filename)
            bot.get_unit_ids_and_location()
            print(bot.current_units)

            if bot.current_phase == "Builds":
                bot.get_possible_builds()
                print(bot.possible_builds)
                print(bot.number_of_builds)
                bot.provide_chat_map_build(filename)


            # look for any other players who might have messaged the bot and get any chat an opp sent that hasn't been read yet. 
            """ to_respond =  bot.get_countryIDs_from_unread_msgs()
            if to_respond:
                msg_and_response = {}
                for country in to_respond:
                    bot.goto_country_chat(country)
                    chat_from_country = bot.get_recent_chat_from_current()
                    print(chat_from_country)"""
            
        print("nothing to do... waiting")
        time.sleep(3600)
    
    input("Press Enter to Close: ")
    bot.close()  


    
    # what does the bot need to do? 
    
    # *first it needs to log onto the page and get into the game* - this is done one time only !!!!! done


    # loop (

    # check the season/stage - have we moved into a new turn? is there something I might need to do? !!!! 

    # check for any unread messages ### provide the messages to a llm for a response ### - save these responses for move options

    # get an image of the current map state ### will also provide this to the llm ### 

    # look for all the moves it might need to make ### provide these to the llm along with the png and the messages from opps ###

    """using outputs from the llm submit moves for the turn

    wait and check to see if the season/stage element updates
    
    )"""
  