# bitbar-yahoo-stocks-advanced

An advanced [xbar](https://xbarapp.com/) (formerly BitBar) plugin that displays stock prices and market data in the macOS menu bar dropdown, powered by the [yfinance](https://github.com/ranaroussi/yfinance) Python library. Forked from [longpdo's Yahoo Stock Ticker](https://github.com/longpdo/bitbar-plugins-custom) and substantially extended with multi-session market data, per-ticker notes, persistent price alerts, debug tooling, and more.

- - -

## Table of Contents

*   Screenshots
*   Requirements
*   Installation
*   Configuration
    *   Watch List & Notes
    *   Sort Order
    *   Visual Options
    *   Debug Mode
*   Features
*   Improvements Over the Original
*   Price Limits
*   How It Works
*   License
*   Credits

- - -

## Requirements

*   **macOS** (uses osascript for alerts, notifications, and prompts)
*   **Python 3**
*   **[xbar](https://xbarapp.com/)** (or SwiftBar / the legacy BitBar)
*   **yfinance** — install before first run:
    
    ```cmake
    pip3 install yfinance
    ```
    

## Installation

1.  Install xbar if you haven't already.
2.  Install the yfinance dependency: `pip3 install yfinance`.
3.  Copy `stocks-advanced.py` into your xbar plugins directory (typically `~/Library/Application Support/xbar/plugins/`).
4.  Rename the file to include a refresh interval in the filename, e.g. `stocks-advanced.18m.py` for an 18-minute refresh cycle.
5.  Make it executable: `chmod +x /path/to/stocks-advanced.py`. (Note: if XBar/BitBar gives you a `Couldn't POSIX Spawn` Error, try also doing `xattr -d com.apple.quarantine /path/to/stocks-advanced.py`.)
6.  Edit the `watch_symbols` dictionary and other configuration variables at the top of the file to suit your portfolio.
7.  Refresh xbar or let it pick up the new plugin automatically.

## Configuration

All user-configurable options are located near the top of the script, above the `CODE STARTING BELOW HERE` comment.

### Watch List & Notes

Stocks are defined as a Python dictionary, where each key is a ticker symbol and each value is a free-text note string. An empty string means no note. Notes are displayed in the submenu for that ticker, prefixed with a 📝 icon, and the same icon appears on the main dropdown line to indicate a note exists.

```python
watch_symbols = {
    'SPY': '',
    'AMZN': '',
    'ASTS': 'Often mentioned alongside RKLB...',
    'GME': '2/3/26 - Maybe buy if drops to 17-19.',
    'NVDA': '',
    # ...
}
```

### Sort Order

The `sort_by` variable controls the display order of tickers in the dropdown.

| Value | Behavior |
| --- | --- |
| `'name'` | Alphabetical by company short name (A → Z) |
| `'symbol'` | Alphabetical by ticker symbol (A → Z) |
| `'market_change_winners'` | Sorted by daily percent change, best performers first |
| `'market_change_losers'` | Sorted by daily percent change, worst performers first |
| `'market_change_volatility'` | Sorted by absolute daily percent change, most volatile first |
| `''` (or any other value) | Preserves the insertion order of `watch_symbols` |

### Visual Options

Several icon and symbol constants can be customized.

| Variable | Default | Purpose |
| --- | --- | --- |
| `NOTESICON` | 📝  | Indicator for tickers that have a user note |
| `PREICON` | 🌅  | Indicator for pre-market session |
| `REGULARICON` | _(empty)_ | Indicator for regular trading session |
| `POSTICON` | 🌛  | Indicator for post-market session |
| `CLOSEDICON` | 💤  | Indicator for closed market |
| `UPARROW` | ▲   | Positive change arrow |
| `DOWNARROW` | ▼   | Negative change arrow |

### Debug Mode

Set `showDebug = True` to enable a **DEBUG** submenu under each ticker. This submenu exposes the raw data dictionary returned by yfinance's `Ticker.info` as well as the script's computed internal variables, formatted as indented dashed text with configurable word-wrapping. Set it to `False` to hide debug information entirely.

## Features

**Menu Bar Display.** The plugin displays a static 💲 icon in the macOS menu bar. Clicking it opens a dropdown listing all watched tickers with their current price and session-appropriate percent change.

**Multi-Session Awareness.** The plugin detects the current market state reported by yfinance — PRE, REGULAR, POST, CLOSED (or PREPRE and POSTPOST, handled as CLOSED) — and adapts its display accordingly. During pre-market hours, prices and percent changes reflect pre-market trading data. During post-market hours, they reflect post-market data. During regular hours, live regular-session data is shown. When the market is closed, the most recent regular-session figures are displayed in gray. Each session state is indicated by its own configurable icon next to the percent change.

**Accurate Regular-Session Close.** Rather than relying solely on the `currentPrice` or `regularMarketPrice` fields from yfinance's `.info` dictionary (which can be stale or reflect extended-hours prices), the plugin calls `Ticker.history()` with one-minute intraday granularity and filters to the 9:30 AM – 4:00 PM window to extract the true regular-session closing price. It falls back to daily close data if intraday data is unavailable.

**Session-Contextual Submenus.** Each ticker's submenu shows detailed price information: previous close, open, bid, ask, day's range, and 52-week range. When the market is in PRE, POST, or CLOSED state, an additional "Regular Close" line appears showing the regular-session closing price and its percent change from the previous close, giving context for how extended-hours prices relate to the day session.

**Per-Ticker Notes.** Each ticker in the watch list can carry a free-text note. Tickers with notes display a 📝 icon on their main dropdown line. The full note text appears word-wrapped in the submenu, making it easy to record buy/sell rationale, links, or reminders directly alongside the price data.

**Persistent Price Alerts.** BUY and SELL price limits can be set through interactive macOS dialogs. When a limit is triggered (current price drops below a BUY limit or rises above a SELL limit), the plugin plays the Glass alert sound five times in succession and then presents a persistent modal dialog box that remains on screen until dismissed. This is significantly more noticeable than a transient notification banner. Triggered limits are automatically removed from the stored limit list.

**Penny Stock Support.** The price limit input validation accepts values with up to four decimal places and does not require a leading digit before the decimal point, accommodating sub-dollar and sub-penny tickers.

**Color Coding.** Positive changes are shown in bold green with an up arrow, negative changes in bold red with a down arrow, and closed-market figures are shown in gray. This uses ANSI escape sequences compatible with xbar's terminal rendering.

**Rate Limiting.** A one-second delay is inserted between consecutive yfinance API calls to avoid triggering rate limits or throttling from Yahoo Finance.

**Debug Introspection.** When debug mode is enabled, each ticker's submenu includes a DEBUG section that pretty-prints the complete raw yfinance `.info` dictionary and the plugin's own computed data structure. The output uses a custom hierarchical dashed-indent format with word-wrapping, making it easy to inspect exactly what data yfinance returned for each ticker without leaving the menu bar.

## Improvements Over the Original

The following is a summary of functional differences between this version and the original `yahoo_stock_ticker.18m.py` by longpdo, determined by comparison of the two codebases.

**Data source replaced.** The original plugin used `curl` to call the Yahoo Finance v7 REST API directly and parsed the JSON response. This version replaces that entirely with the `yfinance` Python library, which handles Yahoo Finance's evolving API endpoints and authentication requirements. The data structure returned by `get_stock_data()` is constructed to be internally consistent, with nested `'raw'` and `'fmt'` sub-dictionaries for each numeric field.

**Pre-market and post-market session support added.** The original treated market state as a binary: either REGULAR (open) or not (closed, shown with a moon emoji). This version recognizes five distinct states — PRE, REGULAR, POST, CLOSED, and PREPRE — and uses a `sessionInfo` configuration dictionary to map each state to its own icon, color scheme, percent-change data field, and off-hours price field. Pre-market and post-market prices and percent changes are fetched from yfinance and displayed when the market is in those sessions.

**Accurate regular-session close price derived from intraday data.** The original relied on the `regularMarketPrice` field from the API response. This version introduces `get_regular_session_close()`, which downloads two days of one-minute intraday bars via `Ticker.history()`, filters to the 9:30–16:00 regular-hours window, and returns the last close within that window. This avoids the problem of `regularMarketPrice` sometimes reflecting extended-hours prices.

**Per-ticker notes system added.** The original stored symbols as a flat list of strings. This version uses a dictionary mapping symbols to note strings. Notes are displayed in the submenu with word-wrapping (via `textwrap.fill`) and flagged with a 📝 icon on the main ticker line.

**Persistent alert notifications.** The original displayed a transient macOS notification banner via `display notification`. This version plays an alert sound five times in rapid succession and then presents a modal `display dialog` that blocks until the user clicks OK, ensuring price alerts are not missed.

**Menu bar display simplified.** The original printed all index tickers (S&P 500, DOW 30, NASDAQ, etc.) directly into the menu bar with live-updating colored change percentages. This version displays only a static 💲 icon in the menu bar, with all ticker data in the dropdown. The index-printing function is present but disabled.

**Symbol sort option added.** The original supported sorting by name, winners, losers, volatility, or custom order. This version adds a `'symbol'` sort option that orders tickers alphabetically by their symbol string.

**Debug submenu added.** A toggleable debug mode exposes the raw yfinance data and the plugin's internal computed variables under each ticker's submenu. The data is formatted using a custom `dashed_json_no_brackets()` function that renders nested dictionaries and lists as indented dashed lines with configurable word-wrapping, suitable for display in xbar's monospaced submenu rendering.

**Regular Close line added to submenu.** When the market is in PRE, POST, or CLOSED state, the submenu displays an additional "Regular Close" line showing the day-session closing price and its percent change from the previous close. The original did not surface this information separately.

**ANSI color scheme updated.** The original used standard-weight green (`\033[32m`) and red (`\033[31m`). This version uses bold green (`\033[1;32m`) and bold red (`\033[1;31m`) for better readability, and introduces bold gray (`\033[1;30m`) for closed-market figures. The font was changed from Menlo to Monaco at size 12.

**Post-market percent change calculated from previous close.** This version computes post-market change percentage relative to the previous day's close (not just relative to the regular-session close), providing a total-day-plus-after-hours return figure in the main dropdown line during post-market hours.

**Penny stock price limit validation.** The original required price limits to match `^\d+(\.\d{1,2})?$` (at least one leading digit, up to two decimal places). This version relaxes the pattern to `^\d*(\.\d{1,4})?$`, allowing values like `.0075` with no leading digit and up to four decimal places.

**Rate limiting between API calls.** This version adds a `time.sleep(1)` call between each ticker's data fetch to avoid overwhelming Yahoo Finance's servers, reducing the risk of throttling or temporary bans. The original made requests with no delay.

**xbar metadata tags.** The plugin metadata uses `<xbar.*>` tags instead of the legacy `<bitbar.*>` tags, reflecting the project's rebrand.

## Price Limits

Price limits let you set BUY and SELL alerts for any tracked symbol. They are stored in a hidden `.db` file alongside the plugin script.

To set a new limit, click **Set new Price Limit...** at the bottom of the dropdown. A series of macOS dialogs will prompt you to select BUY or SELL, choose a symbol, and enter a price. BUY limits trigger when the current price falls below the specified value. SELL limits trigger when the current price rises above it. When triggered, the plugin plays an audible alert and shows a dialog; the limit is then automatically removed.

To remove a specific limit manually, click on it in the **Price Limits** submenu. To clear all limits, click **Clear all Price Limits...**.

## How It Works

The plugin is a Python 3 script executed by xbar at the interval specified in its filename (e.g., every 18 minutes for a `.18m.py` suffix). On each execution, it iterates through the `watch_symbols` dictionary, calls `yfinance.Ticker(symbol).info` for each ticker (with a one-second delay between calls), constructs a normalized data dictionary, checks the current price against any stored BUY/SELL limits, and then prints formatted output to stdout using xbar's plugin protocol. xbar interprets this output to render the menu bar icon and dropdown content.

When invoked with command-line arguments (by xbar in response to user clicks on interactive menu items), the script handles setting new price limits, clearing all limits, or removing individual limits, using macOS osascript dialogs for user interaction.

## License

This project is released under the **MIT License**.

## Credits

*   **Original plugin** by [Long Do (longpdo)](https://github.com/longpdo) — [bitbar-plugins-custom](https://github.com/longpdo/bitbar-plugins-custom)
*   **Advanced version** by [Michael Kupietz (kupietools)](https://github.com/kupietools)
