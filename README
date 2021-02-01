This script is useful for downloading stock market data for a wide range of companies specified by their respective tickers. The script reads in the desired tickers and interacts with yahoo finance to download and save csv files containing information for: Date, Open, High, Low, Close, Adjusted Close, and Volume. Once data for a ticker is downloaded and stored, further requests for data will simply append the most recent information onto the existing csv file. Additionally, each time a user requests downloads, a list of the successful and failed requests will be generated. 

A few important notes:
-Most importantly, HUGE shoutout to https://github.com/bradlucas/get-yahoo-quotes-python for the repo on downloading historic data from yahoo finance. My code is build on top of the work done there, which was a huge time saver.
-Make sure to set up the directories for your ticker_location and csv_location.
-The default behavior is to download as much data that yahoo finance can provide.
-This data is daily historic data

There are 5 command line arguments which may be helpful to facilitate the data download process, which may either be used directly in the terminal, or have their defaults set by modifying the download_data.py script.

Command Line Arguments:

--ticker_location (path): this specifies the file location containing a list of tickers to download data for. The list should be saved as a text file with each ticker on its own new line.

--csv_location (path): this is the directory where csv files should be saved. If this directory does not already exist, create it manually before running the script.

--add_tickers (string): this gives the user an option to add more tickers to their existing list and database. Pass in a string of tickers separated by commas (no spaces) to add the tickers to the list, and download their csv files. The default list of tickers will be updated to contain these new tickers specified. If there is not already a default list of tickers, create this before running the script.

--remove_tickers (string): this gives the user an option to remove tickers from their list and database. Pass in a string of tickers separated by commas (no spaces) to remove the tickers from the list as well as the database (csv_location). If there is not already a default list of tickers, create this before running the script.

--verbose (bool): this provides extra information while downloading data, useful for debugging. Set to false to only see the progress bar for data being downloaded.



To use the script, follow these simple steps.

1. Set up a default list of tickers. This can be a blank text file, or a list of tickers each on their own new line, saved as a text file.
2. Set up a directory to save csv files to.
3. Optionally, change the default ticker_location and csv_location file paths in the script itself.
4. Run the script download_data.py from the command line, or your favorite IDE.

From here, the rest is history (pun intended ;)). When downloading from a pre-saved list of tickers, the computer will open as many threads as it can to speed up this highly parallelizable process to get you your data as quick as possible. Once its finished, you'll find all the data in your csv_location folder!

Now that you have data, you can easily update the files with the latest information at the end of each day, week, or whatever time frame you prefer. Simply run the script in the same way as previously described, and the newest data will be appended to the existing files. If there is a new ticker in your list, the full set of data will be downloaded.


Happy downloading!
