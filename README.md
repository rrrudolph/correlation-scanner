# correlation-scanner
This program is used to find correlated markets for a given instrument. Ultimately all of the correlation data is combined to derive a single index line which will show if the underlying instrument might be under- or over-valued.  Since the process for scanning is essentially a nested loop with each instrument looking at every other instrument, I use threading to read all data into memory up front.  Once that's done, multiprocessing is used to handle the top level loop and threading for the nested loops.  So each instrument is getting its own process, and inside that process is a thread executor to scan all the other instruments.  

The first hurdle to overcome was differing market hours.  My focus was on currencies which are open 24/5, however many of the instruments I use for correlation scanning are only open during the NY session, or about 8/5.  This would have caused much lower correlation scores for those markets and I didn't want that. I decided to align the data on their datetime indexes and only scan periods where both markets were open. 

Once the base instrument (the one that is scanning for correlated markets) is aligned with its corr instrument (the one being scanned), various shift periods are scanned. This is done to find the markets which a regular correlation function might miss.  For example, if Oil tends to lead the price of CAD by n periods, a straightforward scan might return a low correlation score.  However, shifting Oil back by n periods could result in a much higher score.  Also, some of the corr instruments are actually custom spreads like `XLF/XLU` to represent the financial sector in relation to utilities.

After the best shift value is found, only the rows (periods) where correlation breaches the minimum threshold are saved. This results in a somewhat "gappy" Series filled with `nan`s, however this is fine since it will get averaged together with all other correlated instruments.  

Once all the corr markets have been scanned, the different Series' are combined into a Dataframe. From there, I take the average of each to end up with a Dataframe consisting of 2 columns: normalized `close` of the base instrument, and the normalized `close` of the corr markets. The latter gives me a synthetic index which I can use to evaluate the overall correlation to the base instrument.

The image below shows a synthetic index overlayed on a currency chart.  The strategy is to trade divergence between the candles and the line, with the assumption that the line is right and the candles are wrong.  That doesn't always end up being the case, but the reasoning is that if all other markets which are typically correlated to AUDJPY are rising while AUDJPY is falling, it's more likely that a single market is wrong than all the others.

![Screenshot from 2021-06-11 16-37-55](https://user-images.githubusercontent.com/62268115/121751350-8d273800-cad3-11eb-9c96-67d79f85c121.png)

