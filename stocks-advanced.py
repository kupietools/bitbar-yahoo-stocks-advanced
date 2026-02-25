#!/usr/bin/env LC_ALL=en_US.UTF-8 /usr/local/bin/python3
#
# <xbar.title>Yahoo Stock Ticker</xbar.title>
# <xbar.version>v2.01</xbar.version>
# <xbar.author>Long Do,Michael Kupietz</xbar.author>
# <xbar.author.github>longpdo,kupietools</xbar.author.github>
# <xbar.desc>Shows major stock indices in the menu bar and stock symbols in the dropdown menu by pulling data from the Yahoo Finance API. Similar to finance.yahoo.com the prices are delayed, but no API key is necessary. You can also set price alarms for BUY/SELL limits, which will notify you when the limit is reached. This improved version includes per-ticker user notes, more persistent notifications for buy/sell alerts, live data including in the pre-market and post-market sessions, user-settable icons, multi-session price details in the submenus when appropriate, optional debugging information, and no annoying live menu bar updates.</xbar.desc>
# <xbar.image>https://github.com/longpdo/bitbar-plugins-custom/raw/master/images/yahoo-stock-ticker.png</xbar.image>
# <xbar.dependencies>python3</xbar.dependencies>
# <xbar.abouturl>https://github.com/longpdo/bitbar-plugins-custom/blob/master/README.md#yahoo-stock-ticker</xbar.abouturl>
#
# original script by longpdo (https://github.com/longpdo)
# substantial improvements by Michael Kupietz https://github.co/kupietools

# # # IMPORTANT: Make sure to do pip3 install yfinance before first run # # #

#HISTORY:

# Feb 24 2026:
# * Refactor to use categorized watchlist to allow separate menu sections for multiple watchlists
# * Enhanced Menu Bar Icon with options to display icon and/or session icons
# * "Alert" Style Notes indicated with a triangle "!" icon instead of just a document icon
# * Improved Note Formatting so notes are displayed with proper wrapping and consistent font formatting
# * Internal modifications to price limit alerts to accommodate new watchlist dict format
# * Timestamp at top of menu to show last update
# * Standardized variable names to Python standards 
# * Changed default POST and CLOSED session icons. These may change again
# * move yfinance import to top of script so doesn't keep recalling it. 
# * Added option to restore original script's annoying constantly-updating index ticker in the menubar instead of an icon

# Changes from original longpdo version as of mid-February 2026:
# * Use yfinance instead of curl. Now requires user to pip3 install yfinance before first run. 
# * Pre-market and post-market session support added
# * Accurate regular-session close price derived from intraday data via Ticker.history()
# * Per-ticker notes system added
# * Persistent alert notifications instead of temporary banners
# * Menu bar display simplified to an icon, remove indices list and display functions
# * Custom user settings for all icons and session indicators
# * 'Symbol' sort option added
# * Optional 'Debug' submenu added
# * Regular Close line added to submenu when market is not in regular session
# * ANSI color scheme updated for better visibility
# * Post-market percent change calculated from previous close, providing a total-day-plus-after-hours return figure in the main dropdown line during post-market hours.
# * 4-digit Penny stock price limit validation, for prices like 0.2547
# * Rate limiting between API calls
# * Xbar metadata tags. The plugin metadata uses <xbar.*> tags instead of the legacy <bitbar.*> 

from datetime import datetime
from textwrap import fill, wrap
from collections.abc import Mapping, Sequence
import json
import os
import re
import sys
import subprocess
import time
try:
    import yfinance as yf
except ImportError:
    alert('Error', 'Please install yfinance: pip3 install yfinance')
    sys.exit()

# ---------------------------------------------------------------------------------------------------------------------
# BEGIN USER SETTINGS #

# Enter your stock symbols here in the format: {'category':{'symbol1':1symbol1 note', 'symbol2':'symbol2 note'}, ...}. If you don't want to use categories, just make one '' category. 

#Start a note with an exclamation mark ! if you want the ICON_ALERT emoji instead of the NOTEICON emoji

watch_symbols = {
    'Index': {
        '^GSPC': '!1D Vap compression Feb 6 26',
        '^VIX': ''
    },
    'Holding': {
        'AMZN': '',
        'BYND': '',
        'GPK': '',
        'IAU': '',
        'BYND': '',
        'ASTS': 'often mentioned in the same breath as RKLB. https://www.reddit.com/r/stocks/comments/1ptjthh/comment/nvhky8u/ says "I don\'t think RKLB have the same sort of upside as a stock like ASTS with a Starlink-type/high-margin/high-moat TAM opportunity. "',
        'CCJ': '',
        'ONDS': '!It doesn\'t make sense to hold this call. Paying $700 on a $10 call. B/e is $17. Will lose money as long as it stays above 5. Margin on buying 100 shares right now is not much more than $700, margin interest only $60/yr',
        'MCK': '',
        'PEJ': '',
        'PLTR': '',
        'RKLB': 'has been like Palantir and many on reddit feel it\'s a great hold for the next 5 or more years ',
        'WMT': '',
        'V':'',
        'WSR': ''
    },
    'Technical Indicator Watch' : {
        'IGV' : '!Software ETF, has pretty much everything. Moves both up and down slower than individual companies, good during uncertainty. 1hr vap compression Feb 10 2026, 30min on feb 6, 2hr compress on feb 17 but looks like missed the bottom, wait for fan'
    },
    'Top watchlist': {
        'GME': '2/3/26 - Maybe buy if drops to 17-19. Or look at a LEAPS around 24',
        'GOOGL': '',
        'PSLV': '',
        'SNDK': '',
        'RGTI': '',
    },
    'Watchlist': {
        'CHUC': 'Penny stock, look at chart',
        'DRTS': 'see https://www.reddit.com/r/10xPennyStocks/comments/1pp5ldh/the_way_my_father_found_nvidia_back_then_and_you/',
        'EVTL': 'see https://www.reddit.com/r/DoubleBubbler/comments/1oltkcg/why_vertical_aerospace_nyse_evtl_is_worth/ - liable to fall temporarily after planned dilution',
        'KITT': 'Got mentioned but I can\'t find where!',
        'MOBX': 'very speculative. MSCI server blades looks on TV like it might be improving after faltering, mayb worth a LEAP. Earnings nov 4 \'25',
        'NFLX': '',
        'NVDA': '',
        'PSTV': '',
        'RDDT': '',
        'SOXS': '',
        'SOXL': '',
        'WMT':''
    },
    'Penny watchlist': {
    'RIME': 'Penny stock reddit darling right now. Former jukebox now SaaS, very beaten down, some say wrongly. ROC bands slightly up as price slightly fell in 2026',
    'RXT':'Just partnered with PLTR. Pumped to 1.40.'
    }
}

# ICONS
# # Menu Icons
ICON_NOTES = '📝'
ICON_ALERT = '⚠️'
ICON_ARROW_UP='▲'
ICON_ARROW_DOWN='▼'
ICON_MAIN_MENU='💲'
# # Session Icons
ICON_SESSION_PRE='🌅' # Price indicator for AM premarket session
ICON_SESSION_REGULAR='' # Price indicator for day session, default no icon
ICON_SESSION_POST='🌜' # Price indicator for PM postmarket session
ICON_SESSION_CLOSED='😴' # Price indicator for market closed

#MENU DISPLAY OPTIONS
# # Set this to True if you want to show ICON_MAIN_MENU in the menu icon
OPTION_SHOW_MENU_ICON = False

# # Set this to True if you want to show the session icon in the menu icon
#NOTE: This currently uses the first ticker in your first category. If you set this to true, for that first ticker, use a symbol that is updated in all sessions, like ^GSPC or GOOG, not one that only shows during the regular session, like ^VIX, or you won't get get PRE and POST session icons. Maybe later I'll put in an option for which ticker to calculate this from, but for now, this is what you get. 
OPTION_SHOW_SESSION_IN_MENU_ICON = True

# # Enter the order how you want to sort the stock list within each category in the dropbown menu:
# 'name'                     : Sort alphabetically by company name from A to Z
# 'symbol'                   : Sort alphabetically by symbol from A to Z
# 'market_change_winners'    : Sort by value from top winners to losers
# 'market_change_losers'     : Sort by value from top losers to winners
# 'market_change_volatility' : Sort by absolute value from top to bottom
# '' or other values         : Sort by your custom order from the symbols array above
SORT_BY = 'market_change_winners'

# # Set this True or False to turn on or off Debug submenu under each ticker's detail info. Capitalization counts.
OPTION_SHOW_DEBUG_SUBMENU = False

#ANNOYING LIVE INDICES TICKER IN MENUBAR OPTION
# # To have huge annoying live index ticker updates flash in your menu bar instead the menu icons, set this True
OPTION_SHOW_ANNOYING_INDICES_IN_MENU = False

# # This is number of seconds it waits before annoying updates if OPTION_SHOW_ANNOYING_INDICES_IN_MENU is True; must be > 0
OPTION_SHOW_ANNOYING_INDICES_IN_MENU_INTERVAL = 5

# # This is the indices list shown in your menu bar if OPTION_SHOW_ANNOYING_INDICES_IN_MENU is True
INDICES_DICT = {
    '^GSPC': '🇺🇸 S&P 500',
    '^DJI': '🇺🇸 DOW 30',
    '^IXIC': '🇺🇸 NASDAQ',
    '^GDAXI': '🇩🇪 DAX',
    '^FTSE': '🇬🇧 FTSE 100',
    '^FCHI': '🇫🇷 CAC 40',
    '^STOXX50E': '🇪🇺 EURO STOXX 50',
 }

# MENU FONTS

MENU_FONT = "Monaco" # Main menu
MENU_FONT_SIZE = "12" # Main menu
NOTES_FONT = "Monaco" #Notes in submenu, when present
NOTES_FONT_SIZE = "11" #Notes in submenu, when present


# END USER SETTINGS

# ---------------------------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------------------------------
# CODE STARTING BELOW HERE, DO NOT EDIT IF YOU ARE A REGULAR USER
# Constants

ANSI_GREEN = '\033[1;32m' #was '\033[32m' but this is too light and not readable
ANSI_RED = '\033[1;31m'
ANSI_RESET = '\033[0m'
ANSI_GRAY = '\033[1;30m'
    
SESSION_INFO = {
    'PRE':{
        'marketStateName':'PRE',
        'greenArrow':ANSI_GREEN + ICON_ARROW_UP,
        'noArrow':' ',
        'redArrow':ANSI_RED + ICON_ARROW_DOWN,
        'chgPctKeyName':'preMarketChangePercent',
        'icon':ICON_SESSION_PRE,
        'offHoursPriceName':'preMarketPrice',
        'menuicon':ICON_SESSION_PRE
    },
    'REGULAR':{
        'marketStateName':'OPEN',
        'greenArrow':ANSI_GREEN + ICON_ARROW_UP,
        'noArrow':' ',
        'redArrow':ANSI_RED + ICON_ARROW_DOWN,
        'chgPctKeyName':'regularMarketChangePercent',
        'icon':ICON_SESSION_REGULAR,
        'offHoursPriceName':'',
        'menuicon':''
    },
    'POST':{
        'marketStateName':'POST',
        'greenArrow':ANSI_GREEN + ICON_ARROW_UP,
        'noArrow':' ',
        'redArrow':ANSI_RED + ICON_ARROW_DOWN,
        'chgPctKeyName':'postMarketChangePercent',
        'icon':ICON_SESSION_POST,
        'offHoursPriceName':'postMarketPrice',
        'menuicon':ICON_SESSION_POST
    },
    'CLOSED':{
        'marketStateName':'CLOSED',
        'greenArrow':ANSI_GRAY + ICON_ARROW_UP,
        'noArrow':ANSI_GRAY + ' ',
        'redArrow':ANSI_GRAY + ICON_ARROW_DOWN,
        'chgPctKeyName':'regularMarketChangePercent',
        'icon':ICON_SESSION_CLOSED,
        'offHoursPriceName':'',
        'menuicon':ICON_SESSION_CLOSED
    }
}
    
categories = list(watch_symbols)

FONT = "| font="+MENU_FONT+" size="+MENU_FONT_SIZE
FONT_SMALL = "| font="+NOTES_FONT+" size="+NOTES_FONT_SIZE

# ---------------------------------------------------------------------------------------------------------------------

# macOS Alerts, Prompts and Notifications -----------------------------------------------------------------------------
# Display a macOS specific alert dialog to get confirmation from user to continue
def alert(alert_title='', alert_text='', alert_buttons=['Cancel', 'OK']):
    try:
        d = locals()
        user_input = subprocess.check_output(['osascript', '-l', 'JavaScript', '-e', '''
            const app = Application.currentApplication()
            app.includeStandardAdditions = true
            const response = app.displayAlert('{alert_title}', {{
                message: '{alert_text}',
                as: 'critical',
                buttons: ['{alert_buttons[0]}', '{alert_buttons[1]}'],
                defaultButton: '{alert_buttons[1]}',
                cancelButton: '{alert_buttons[0]}'
            }})
            response
        '''.format(**d)]).decode('ascii').rstrip()
        return user_input
    except subprocess.CalledProcessError:
        pass


# Display a macOS specific prompt dialog to get text input from the user
def prompt(prompt_text=''):
    try:
        d = locals()
        user_input = subprocess.check_output(['osascript', '-l', 'JavaScript', '-e', '''
            const app = Application.currentApplication()
            app.includeStandardAdditions = true
            const response = app.displayDialog('{prompt_text}', {{
                defaultAnswer: '',
                buttons: ['Cancel', 'OK'],
                defaultButton: 'OK'
            }})
            response.textReturned
        '''.format(**d)]).decode('ascii').rstrip()
        if user_input == '':
            sys.exit()
        return user_input
    except subprocess.CalledProcessError:
        pass


# Display a macOS specific prompt dialog prompting user for a choice from a list
def prompt_selection(prompt_text='', choices=''):
    try:
        d = locals()
        user_selection = subprocess.check_output(['osascript', '-l', 'JavaScript', '-e', '''
            const app = Application.currentApplication()
            app.includeStandardAdditions = true
            var choices = {choices}
            const response = app.chooseFromList(choices, {{
                withPrompt: '{prompt_text}',
                defaultItems: [choices[0]]
            }})
            response
        '''.format(**d)]).decode('ascii').rstrip()
        if user_selection == 'false':
            sys.exit()
        return user_selection
    except subprocess.CalledProcessError:
        pass


# FIRST TRY Display a macOS specific notification
# def notify(text, title, subtitle, sound='Glass'):
#      cmd = 'osascript -e \'display notification "{}" with title "{}" subtitle "{}" sound name "{}"\''
#     os.system(cmd.format(text, title, subtitle, sound))

# SECOND TRY Display a macOS specific notification with alert dialog
# def notify(text, title, subtitle, sound='Glass'):
#     # Play sound multiple times to get attention
#     for i in range(5):
#         os.system(f'afplay /System/Library/Sounds/{sound}.aiff')
#         time.sleep(0.3)
    
    # Show persistent alert dialog that stays until dismissed
    try:
        subprocess.call(['osascript', '-e', f'''
            display dialog "{text}\\n\\n{subtitle}" with title "{title}" buttons {{"OK"}} default button "OK" with icon caution
        '''])
    except:
        pass    

def notify(text, title, subtitle, sound='Glass'):
    # Play sound multiple times to get attention
    for i in range(5):
        os.system(f'afplay /System/Library/Sounds/{sound}.aiff')
        time.sleep(0.3)
    
    # Show persistent alert dialog that stays until dismissed
    subprocess.call(['osascript', '-e', f'''
        display dialog "{text}\\n\\n{subtitle}" with title "{title}" buttons {{"OK"}} default button "OK" with icon caution
    '''], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------------------------------------------------------------


# Methods to read, write, remove data from the hidden .db file --------------------------------------------------------
def read_data_file(data_file):
    with open(data_file, 'r') as f:
        content = f.readlines()
    f.close()
    content = [x.strip() for x in content]
    return content


def write_data_file(data_file, limit_type, symbol, price):
    with open(data_file, 'a') as f:
        f.write(limit_type + ' ' + symbol + ' ' + price + '\n')
    f.close()


def remove_line_from_data_file(data_file, line_to_be_removed):
    with open(data_file, 'r') as f:
        content = f.readlines()
    with open(data_file, 'w') as f:
        for line in content:
            if line.strip('\n') != line_to_be_removed:
                f.write(line)
    f.close()
# ---------------------------------------------------------------------------------------------------------------------

def get_regular_session_close(t):

    intraday = t.history(period="2d", interval="1m", auto_adjust=False)
    if intraday is None or intraday.empty:
        return 0

    intraday = intraday.sort_index()
    last_day = intraday.index[-1].date()
    day = intraday[intraday.index.date == last_day]

    regular = day.between_time("09:30", "16:00")
    if regular.empty:
        # fallback to daily
        daily = t.history(period="10d", interval="1d", auto_adjust=False)
        return float(daily["Close"].iloc[-1]) if not daily.empty else 0

    return float(regular["Close"].iloc[-1])


def get_stock_data(symbol):
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        """
        NOTE: .info isn't the greatest way to do this... .download() would fetch more at once, but then you have to calculate current prices and I *just* got all this working the way I wanted to. .fast_info is also supposedly more reliable, but I haven't had any problems, so, leaving it. 
        """
        
        # Get current price and other data
        regular_market_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        #need to jump through hoops with a function to get today's regular session close. 
        regular_market_price = get_regular_session_close(ticker)

        # WAS, BUT CHAGPT SAYS NOT RIGHT, regularMarketPreviousClose IS MORE RELIABLE. previous_close = info.get('previousClose', 0)
        previous_close = info.get('regularMarketPreviousClose') or info.get('previousClose', 0)
        
        # Get pre-market and post-market data
        pre_market_price = info.get('preMarketPrice', 0)
        post_market_price = info.get('postMarketPrice', 0)
        
        if info.get('marketState', 'CLOSED') == "PRE" and pre_market_price:
            current_price = pre_market_price
        elif info.get('marketState', 'CLOSED') == "POST" and post_market_price:
            current_price = post_market_price
        else:
            current_price = regular_market_price
                
        if previous_close > 0:
            change_percent = ((regular_market_price - previous_close) / previous_close) * 100
            pre_change_percent = ((pre_market_price - previous_close) / previous_close) * 100 if pre_market_price > 0 else 0
            post_change_percent = ((post_market_price - regular_market_price) / regular_market_price) * 100 if post_market_price > 0 else 0
            post_change_percent_since_yesterday = ((post_market_price - previous_close) / previous_close) * 100 if post_market_price > 0 else 0

        else:
            change_percent = 0
            pre_change_percent = 0
            post_change_percent = 0
        
        # Create a compatible data structure matching the original format
        stock_data = {
            'price': {
                'symbol': symbol,
                'shortName': info.get('shortName', symbol),
                'longName': info.get('longName', info.get('shortName', symbol)),
                'currentPrice': {'raw': current_price, 'fmt': f"{current_price:.2f}"},
                'regularMarketPrice': {'raw': regular_market_price, 'fmt': f"{regular_market_price:.2f}"},
                'regularMarketTime': int(info.get('regularMarketTime', 0)),
                'regularMarketChangePercent': {'raw': change_percent, 'fmt': f"{change_percent:.2f}%"},
                'regularMarketChange': {'raw': regular_market_price - previous_close, 'fmt': f"{regular_market_price - previous_close:.2f}"},
                'regularMarketOpen': {'raw': info.get('regularMarketOpen', 0), 'fmt': f"{info.get('regularMarketOpen', 0):.2f}"},
                'regularMarketPreviousClose': {'raw': previous_close, 'fmt': f"{previous_close:.2f}"},
                'marketState': info.get('marketState', 'CLOSED'),
                'currency': info.get('currency', 'USD'),
                # Add pre-market and post-market data
                'preMarketPrice': {'raw': pre_market_price, 'fmt': f"{pre_market_price:.2f}"},
                'preMarketChangePercent': {'raw': pre_change_percent, 'fmt': f"{pre_change_percent:.2f}%"},
                'postMarketPrice': {'raw': post_market_price, 'fmt': f"{post_market_price:.2f}"},
                'postMarketChangePercent': {'raw': post_change_percent_since_yesterday, 'fmt': f"{post_change_percent_since_yesterday:.2f}%"}
            },
            'summaryDetail': {
                'regularMarketDayHigh': {'raw': info.get('dayHigh', 0), 'fmt': f"{info.get('dayHigh', 0):.2f}"},
                'regularMarketDayLow': {'raw': info.get('dayLow', 0), 'fmt': f"{info.get('dayLow', 0):.2f}"},
                'fiftyTwoWeekHigh': {'raw': info.get('fiftyTwoWeekHigh', 0), 'fmt': f"{info.get('fiftyTwoWeekHigh', 0):.2f}"},
                'fiftyTwoWeekLow': {'raw': info.get('fiftyTwoWeekLow', 0), 'fmt': f"{info.get('fiftyTwoWeekLow', 0):.2f}"},
                'bid': {'raw': info.get('bid', 0), 'fmt': f"{info.get('bid', 0):.2f}" if info.get('bid') else 'N/A'},
                'ask': {'raw': info.get('ask', 0), 'fmt': f"{info.get('ask', 0):.2f}" if info.get('ask') else 'N/A'}
            },
                'rawData': info
        }
        
        return stock_data
        
    except Exception as e:
        alert('Error', f'Failed to fetch data for {symbol}: {str(e)}')
        sys.exit()              

# Check a given stock symbol against the price limit list
def check_price_limits(symbol_to_be_checked, current_price, price_limit_list, data_file):
    for limit_entry in price_limit_list:
        if symbol_to_be_checked in limit_entry:
            # Get the limit price, limits are saved in the format: TYPE SYMBOL PRICE
            limit_price = float(limit_entry.split()[2])
            notification_text = symbol_to_be_checked + ' current price is: ' + str(current_price)
            notification_title = 'Price Alarm'

            # Notify user if current price is lower than the BUY limit, then remove the limit from list
            if 'BUY' in limit_entry and current_price < limit_price:
                notification_subtitle = 'BUY Limit: ' + str(limit_price)
                notify(notification_text, notification_title,
                       notification_subtitle)
                remove_line_from_data_file(data_file, limit_entry)

            # Notify user if current price is higher than the SELL limit, then remove the limit from list
            if 'SELL' in limit_entry and current_price > limit_price:
                notification_subtitle = 'SELL Limit: ' + str(limit_price)
                notify(notification_text, notification_title,
                       notification_subtitle)
                remove_line_from_data_file(data_file, limit_entry)



def print_index(s, name): 
#restored from older version as of v2.0; I've made turning it on or off it a user option
    market_state = index['price']['marketState']
    effective_market_state = get_eff_market_state(market_state)
    #NOTE: yfinance sometimes returns PREPRE and POSTPOST sessions, but no dedicated info for these sessions. effective_market_state ensures anything but PRE, POST, or REGULAR is handled as CLOSED.
    off_name = SESSION_INFO.get(effective_market_state, {}).get('offHoursPriceName') 
    change = index['price']['regularMarketChangePercent']['raw']
    raw_price = (
        s.get('price', {})
         .get(off_name, {})
         .get('raw')
    ) #get() allows nonexistent keys, not every session has s['price'][SESSION_INFO[market_state]['offHoursPriceName']]['raw'], which is how raw_price would be looked up if those keys never failed

    color=''
    
    # Setting color and emojis depending on the market state and the market change
    if (effective_market_state in ('PRE','POST') and raw_price) or effective_market_state=='REGULAR':
        # Set color for positive and negative values
        color = ''
        if change > 0:
            color = SESSION_INFO[effective_market_state]['greenArrow']
        if change < 0:
            color = SESSION_INFO[effective_market_state]['redArrow']
        if change == 0:
            color = SESSION_INFO[effective_market_state]['noArrow']
        # Format change to decimal with a precision of two and reset ansi color at the end
        change_in_percent = '(' + \
            s['price'][SESSION_INFO[effective_market_state]['chgPctKeyName']]['fmt'] + ')'
        colored_change = SESSION_INFO[effective_market_state]['icon'] + ' ' + color + change_in_percent + ANSI_RESET
    else: #market_state == 'CLOSED':
        # Set change with a moon emoji for closed markets
        colored_change = ICON_SESSION_CLOSED + \
            '(' + index['price'][SESSION_INFO[effective_market_state]['chgPctKeyName']]['fmt'] + ') '

    # Print the index info only to the menu bar
    print(name, colored_change, '| dropdown=false', sep=' ')


# Custom indenting to print debug info if desired

def dashed_json_no_brackets(
    obj,
    base="------",
    step="--",
    *,
    sort_keys=True,
    ensure_ascii=False,
    wrap_width=None,                 # e.g. 120 (None disables wrapping)
    long_value_on_next_line=False,   # if True and value length > wrap_width, put value on next line
    wrap_long_values_only=True,      # wrap only strings by default (not numbers/bools/null)
):
    """
    Dashed nesting per level with optional wrapping for long values.

    Structure:
    - Dict key lines:  <prefix>"key": <value>   OR   <prefix>"key":
    - Lists: each item gets a submenu header: <prefix>[i]:
    - No standalone container lines like '{', '}', '[', ']', '[]', '{}'
    - Empty dict/list values are skipped.

    Wrapping:
    - If wrap_width is not None, long scalar values can be wrapped.
    - If long_value_on_next_line is True, long values are printed starting on the next line
      at one additional nesting level (adds one extra `step`), and wrapped lines keep that level.
    """

    def is_listlike(x):
        return isinstance(x, Sequence) and not isinstance(x, (str, bytes, bytearray))

    def p(level: int) -> str:
        return base + (step * level)

    def jd(x):
        return json.dumps(x, ensure_ascii=ensure_ascii)

    def is_scalar(x):
        return isinstance(x, (str, int, float, bool)) or x is None

    def should_wrap_value(v):
        if wrap_width is None:
            return False
        if wrap_long_values_only and not isinstance(v, str):
            return False
        # measure the printable JSON token length (includes quotes/escapes for strings)
        return len(jd(v)) > wrap_width

        # simpler version, hard break at n characters   def wrap_text(s: str, width: int):
        #       """Hard wrap every `width` chars (keeps it simple, no truncation)."""
        #       return [s[i:i + width] for i in range(0, len(s), width)] if s else [""]

    def wrap_text(s: str, width: int):
        """
        Wrap text preferring spaces/hyphens; only break long 'words' if necessary
        to enforce the width.
        """
        if s is None:
            return [""]

        s = str(s)
        if width is None or width <= 0:
            return [s]
        if s == "":
            return [""]

        # 1) Prefer breaking on whitespace (and hyphens), don't split words.
        chunks = wrap(
            s,
            width=width,
            break_long_words=False,
            break_on_hyphens=True,
            drop_whitespace=False,
        )

        # 2) If there were no break opportunities (e.g. one enormous token),
        # fall back to breaking long words so we still respect the width.
        if len(chunks) == 1 and len(chunks[0]) > width:
            chunks = wrap(
                s,
                width=width,
                break_long_words=True,
                break_on_hyphens=True,
                drop_whitespace=False,
            )

        return chunks if chunks else [""]
        
    lines = []

    def emit_wrapped_json_token(level: int, token: str):
        """Emit a pre-rendered JSON token, wrapped; all continuation lines keep the same level."""
        if wrap_width is None or len(token) <= wrap_width:
            lines.append(p(level) + token)
            return
        for chunk in wrap_text(token, wrap_width):
            lines.append(p(level) + chunk)

    def emit_key_value(k, v, level: int):
        # # suppress empty containers
        # if isinstance(v, Mapping) and not v:
        #    return
        # if is_listlike(v) and len(v) == 0:
        #    return

        ktxt = jd(k)

        # container values => submenu
        if isinstance(v, Mapping) or is_listlike(v):
            lines.append(p(level) + f"{ktxt}:")
            walk(v, level + 1)
            return

        # scalar value
        vtok = jd(v)

        if should_wrap_value(v) and long_value_on_next_line:
            # key line only, value starts on next line with extra indent level
            lines.append(p(level) + f"{ktxt}:")
            emit_wrapped_json_token(level + 1, vtok)
        elif should_wrap_value(v):
            # keep key + first part on same line if possible by wrapping the *whole* "key: value" token
            # so every wrapped continuation line has the SAME prefix level
            whole = f"{ktxt}: {vtok}"
            emit_wrapped_json_token(level, whole)
        else:
            lines.append(p(level) + f"{ktxt}: {vtok}")

    def walk(x, level: int):
        # Scalars at root / list items
        if is_scalar(x):
            emit_wrapped_json_token(level, jd(x))
            return

        # Dict
        if isinstance(x, Mapping):
            if not x:
                return
            lines.append(p(level) + "{")
            items = x.items()
            if sort_keys:
                items = sorted(items, key=lambda kv: str(kv[0]))
            for k, v in items:
                emit_key_value(k, v, level)
            lines.append(p(level) + "}")    
            return

        # List
        if is_listlike(x):
            if len(x) == 0:
                return
            lines.append(p(level) + "[")    
            for i, item in enumerate(x):
                lines.append(p(level) + f"[{i}]:")
                walk(item, level + 1)
            lines.append(p(level) + "]")
            return

        # Fallback (unexpected types)
        emit_wrapped_json_token(level, jd(str(x)))

    walk(obj, 0)
    return "\n".join(lines)

# Set effective market state
def get_eff_market_state(market_state):
    this_state = market_state if market_state in ('PRE','REGULAR','POST') else 'CLOSED'
    return this_state

# Print the stock info in the dropdown menu with additional info in the submenu
def print_stock(s,category):
    market_state = s['price']['marketState']
    change = s['price']['regularMarketChangePercent']['raw']

    # Setting color and emojis depending on the market state and the market change
    # Now using dict with info for sessions rather than separate conditionals as in original
    effective_market_state = get_eff_market_state(market_state)
    off_name = SESSION_INFO.get(effective_market_state, {}).get('offHoursPriceName') 
    raw_price = (
        s.get('price', {})
         .get(off_name, {})
         .get('raw')
    ) #get() allows nonexistent keys, not every session has s['price'][SESSION_INFO[market_state]['offHoursPriceName']]['raw'], which is how raw_price would be looked up if those keys never failed
    color = ''
    #NOTE: yfinance sometimes returns PREPRE and POSTPOST sessions, but no dedicated info for these sessions. effective_market_state ensures anything but PRE, POST, or REGULAR is handled as CLOSED.
    
    # Setting color and emojis depending on the market state and the market change
    if (effective_market_state in ('PRE','POST') and raw_price) or effective_market_state=='REGULAR':
        # Set color for positive and negative values       
        market = SESSION_INFO[effective_market_state]['marketStateName']
        if change > 0:
            color = SESSION_INFO[effective_market_state]['greenArrow']
        if change < 0:
            color = SESSION_INFO[effective_market_state]['redArrow']
        if change == 0:
            color = SESSION_INFO[effective_market_state]['noArrow']
        # Format change to decimal with a precision of two and reset ansi color at the end
        change_in_percent = '(' + \
            s['price'][SESSION_INFO[effective_market_state]['chgPctKeyName']]['fmt'] + ')'
        colored_change = SESSION_INFO[effective_market_state]['icon'] + ' ' + color + change_in_percent + ANSI_RESET
    else: #if market_state == 'CLOSED':
        market = SESSION_INFO[effective_market_state]['marketStateName']
        # Set change with a moon emoji for closed markets
        colored_change = SESSION_INFO[effective_market_state]['icon'] + ' ' + \
            '(' + s['price'][SESSION_INFO[effective_market_state]['chgPctKeyName']]['fmt'] + ') '
    

    # Remove appending stock exchange symbol for foreign exchanges, e.g. Apple stock symbol in Frankfurt: APC.F -> APC
    symbol = s['price']['symbol'].split('.')[0]
    # Convert epoch to human readable time HH:MM:SS
    time = datetime.fromtimestamp(
        s['price']['regularMarketTime']).strftime('%X')

    regular_market_day_high = s['summaryDetail']['regularMarketDayHigh']['raw']
    regular_market_day_low = s['summaryDetail']['regularMarketDayLow']['raw']
    regular_market_day_range = regular_market_day_high - regular_market_day_low

    fifty_two_week_high = s['summaryDetail']['fiftyTwoWeekHigh']['raw']
    fifty_two_week_low = s['summaryDetail']['fiftyTwoWeekLow']['raw']
    fifty_two_week_range = fifty_two_week_high - fifty_two_week_low

    # Print the stockf seen in the dropdown menu
    stock_info = '{:<5} {:>10} {:<10}' + ((' '+ICON_NOTES if watch_symbols[category][symbol][0] != "!" else ICON_ALERT) if watch_symbols[category][symbol] != '' else '') + FONT
    print(stock_info.format(
        symbol, s['price']['currentPrice']['fmt'], colored_change))
    # Print additional stock info in the submenu
    LDOTS="........................."
    stock_submenu = '{:<20.20} {:<17}' + FONT
    print('--' + s['price']['shortName'] + FONT)
    print('--' + s['price']['longName'] +
          ' - Currency in ' + s['price']['currency'] + FONT)
    print('--' + time + ' - Market is ' + market + FONT)
    print('-----')
    print(stock_submenu.format('--Previous Close:'+LDOTS,
          s['price']['regularMarketPreviousClose']['fmt']))
    print(stock_submenu.format(
        '--Open:'+LDOTS, s['price']['regularMarketOpen']['fmt']))
    if market_state in ("POST","CLOSED","PRE"):
        print(stock_submenu.format('--Regular Close:'+LDOTS, s['price']['regularMarketPrice']['fmt'] + \
            ' (' + s['price']['regularMarketChangePercent']['fmt'] + ')'))
    print(stock_submenu.format('--Bid:'+LDOTS, s['summaryDetail']['bid']['fmt']))
    print(stock_submenu.format('--Ask:'+LDOTS, s['summaryDetail']['ask']['fmt']))
    print(stock_submenu.format('--Day\'s Range:'+LDOTS,
          '{:.2f}'.format(regular_market_day_range)))
    print(stock_submenu.format('--52 Week Range:'+LDOTS,
          '{:.2f}'.format(fifty_two_week_range)))
    print('-----')
    if watch_symbols[category][symbol] != '':
        theNote = fill('--'+ICON_NOTES+' Notes: '+ watch_symbols[category][symbol],width=60,subsequent_indent="--")
        print('\n'.join(line + FONT_SMALL for line in theNote.splitlines())) 
        #only way to suffix every line created with fill()
        print('-----')
    if OPTION_SHOW_DEBUG_SUBMENU:
        print('--DEBUG')
        print(stock_submenu.format('----postMarketPrice',s['price']['postMarketPrice']['raw']))
        print('----raw yfinance info')
        print(dashed_json_no_brackets(s['rawData'],wrap_width=60, long_value_on_next_line=True))
        print('----script variables')
        slocal = { 'price':s['price'], 'summaryDetail':s['summaryDetail'] }
        print(dashed_json_no_brackets(slocal,wrap_width=60, long_value_on_next_line=True))

# Print the price limits in the dropdown menu
def print_price_limits(price_limit_list):
    PARAMETERS = FONT + " refresh=true terminal='false' bash='" + __file__ + "'"

    print('---')
    print('Price Limits' + FONT)
    # Print available price limits in the submenu
    for limit_entry in price_limit_list:
        # Split the limit entry, limits are saved in the format: TYPE SYMBOL PRICE
        limit_type = limit_entry.split()[0]
        symbol = limit_entry.split()[1]
        limit_price = limit_entry.split()[2]
        price_limit_submenu = '{:<6} {:<4} {:<10}'
        # Print the price limit data into the submenu
        # onClick will rerun this script with parameters 'remove' and the {limit_entry} to remove clicked the limit
        print(price_limit_submenu.format('--' + limit_type, symbol, limit_price +
              PARAMETERS + " param1='remove' param2='" + limit_entry + "'"))
    print('-----')
    print('--To remove a limit, click on it.' + FONT)
    # Print the clickable fields to set new limits or clear all price limits
    # onClick will rerun this script with parameters 'set' to set a new limit
    print('Set new Price Limit...' + PARAMETERS + " param1='set'")
    # onClick will rerun this script with parameters 'clear' to clear the hidden .db file
    print('Clear all Price Limits...' + PARAMETERS + " param1='clear'")


if __name__ == '__main__':
    data_file = os.path.join(os.path.dirname(os.path.realpath(
        __file__)), '.' + os.path.basename(__file__) + '.db')

    # Normal execution by BitBar without any parameters
    if len(sys.argv) == 1:
       
        # Check if hidden .db file exists
        try:
            price_limit_list = read_data_file(data_file)
        except FileNotFoundError:
            price_limit_list = []

        # Print the menu bar information
        # restored for version 2.0; I've made turning it on or off it a user option. 
        if OPTION_SHOW_ANNOYING_INDICES_IN_MENU:
            for symbol, name in INDICES_DICT.items():
                time.sleep(OPTION_SHOW_ANNOYING_INDICES_IN_MENU_INTERVAL)  # 1 second delay between requests
                index = get_stock_data(symbol)
                print_index(index, name)

        # Print icon in the menu bar
        
        first_category_name, first_symdict = next(iter(watch_symbols.items()))
        first_stock = next(iter(first_symdict))  # dict iterates over keys by default


        first_stock_data=get_stock_data(first_stock)
        menu_market_state = get_eff_market_state(first_stock_data['price']['marketState'])
        session_menu_icon=SESSION_INFO[menu_market_state]['menuicon'] 
        print((ICON_MAIN_MENU if (OPTION_SHOW_MENU_ICON or (OPTION_SHOW_SESSION_IN_MENU_ICON and not session_menu_icon)) else '') + (session_menu_icon if OPTION_SHOW_SESSION_IN_MENU_ICON else ''))
        # make sure to at least show menuicon if session menu icon is enabled but the menu icon for the current session is blank 

        currtime = datetime.now()
        print("---")
        print("As of " + currtime.strftime("%Y-%m-%d %H:%M:%S"))

        for category in watch_symbols:
            category_symbols = watch_symbols[category].keys()
            stocks = []
                
            # For each symbol: curl the data, check against the .db file for limits
            for symbol in category_symbols:
                time.sleep(1)  # 1 second delay between requests
                stock = first_stock_data if first_stock_data else get_stock_data(symbol)
                first_stock_data = {}
                stocks.append(stock) 
                check_price_limits(
                    symbol, stock['price']['currentPrice']['raw'], price_limit_list, data_file)

            
            # Set order of stocks
            if SORT_BY == 'name':
                stocks = sorted(stocks, key=lambda k: k['price']['shortName'])
            if SORT_BY == 'symbol':
                stocks = sorted(stocks, key=lambda k: k['price']['symbol'])
            if SORT_BY == 'market_change_winners':
                stocks = sorted(
                    stocks, key=lambda k: k['price']['regularMarketChangePercent']['raw'], reverse=True)
            if SORT_BY == 'market_change_losers':
                stocks = sorted(
                    stocks, key=lambda k: k['price']['regularMarketChangePercent']['raw'])
            if SORT_BY == 'market_change_volatility':
                stocks = sorted(stocks, key=lambda k: abs(
                    k['price']['regularMarketChangePercent']['raw']), reverse=True)

            # Print the stock information inside the dropdown menu
            print('---')
            if (category != ''):
                print (category+":"+FONT)
            for stock in stocks:
                print_stock(stock,category)

        # Print the price limit section inside the dropdown
        print_price_limits(price_limit_list)

    # Script execution with parameter 'set' to set new price limits
    if len(sys.argv) == 2 and sys.argv[1] == 'set':
        # Run this until user does not want to continue
        while True:
            # Get the user selection of whether he wants to set 'BUY' or 'SELL'
            limit_type_prompt = 'Select the type of your limit: BUY (SELL) limits are triggered, when the price is lower (higher) than the limit.'
            limit_type_choices = '["BUY", "SELL"]'
            limit_type = prompt_selection(
                limit_type_prompt, limit_type_choices)
                
            # begin generate symbols variable as appeared in the original script instead of watch_symbols before I added categories
            symbols = sorted({sym for symdict in watch_symbols.values() for sym in symdict.keys()})
            symbols_js = json.dumps(all_symbols) #safer than dumping a python list into JXA as done in prompt_selection

            # Get the user selection of all tracked symbols
            symbol = prompt_selection('Select stock symbol:', symbols_js)

            # Get the user input for a price limit, info message includes the current market price
            #price = prompt('Current price of ' + symbol + ' is ' + str(get_stock_data(
            #    symbol)['regularMarketPrice']) + '. Enter a value for your price limit.')
            price = prompt('Current price of ' + symbol + ' is ' + str(get_stock_data(
                symbol)['price']['currentPrice']['raw']) + '. Enter a value for your price limit.')

            # Check if the user input are decimals with a precision of two
            if not re.match(r'^\d*(\.\d{1,4})?$', price): # Prices can have no leading digit or 4 decimals, for penny stocks! Was re.match(r'^\d+(\.\d{1,2})?$', price):
                # Alert the user on invalid value and stop the script
                alert('Error', 'You entered an invalid value: ' + price +
                      ' - valid values are decimals with a precision of 2, e.g 25.70!')
                sys.exit()

            # Write the limit to the hidden .db file
            write_data_file(data_file, limit_type, symbol, price)

            # Ask user if he wants to add another limit
            add_another_limit = alert(
                'Question', 'Do you want to add another price limit?', ['No', 'Yes'])
            # If the user clicked the 'No' button, stop the script
            if add_another_limit is None:
                sys.exit()

    # Script execution with parameter 'clear' to clear the .db file
    if len(sys.argv) == 2 and sys.argv[1] == 'clear':
        # Ask for user confirmation
        warning = alert(
            'Warning', 'This will clear your price limits! Do you want to continue?')
        if warning is None:
            sys.exit()

        # Clear the file
        open(data_file, 'w').close()

    # Script execution with the parameters 'remove' and the line to be removed
    if len(sys.argv) == 3 and sys.argv[1] == 'remove':
        limit_to_be_removed = sys.argv[2]
        remove_line_from_data_file(data_file, limit_to_be_removed)
