# correlation-scanner
This program is used to find correlated markets for a given instrument. Ultimately all of the correlated markets are combined to derive a single index line which will show if the underlying instrument might be under- or over-valued. 

The first issue to overcome was differing market hours.  My focus was on currencies which are open 24/5, however many of the instruments I use for correlation scanning are only open during the NY session, or about 8/5.  This would have caused much lower correlation scores for those markets and I didn't want that. I decided to align the data on their indexes and only scan periods where both markets were open. 

Once the base instrument (the one that is scanning for correlated markets) is aligned with its corr instrument (the one being scanned), various shift periods are scanned. This is done to find the markets which a regular correlation function might miss.  For example, if Oil tends to lead the price of CAD by n periods, a straightforward scan might return a low correlation score.  However, shifting Oil back by n periods could result in a much higher score.

Once the best shift value is found, only the rows (periods) where correlation breaches the minimum threshold are saved. This results in a somewhat "gappy" Series filled with nans, however this is fine since I intended for the program to ignore correlated markets relatively quickly if their correlation score dropped.

After all the corr markets have been scanned, their Series are used as columns in a single Dataframe. From there, I take the average of each to end up with a Dataframe consisting of 2 columns: normalized Close of the base instrument, and the normalized Close of the corr markets. The latter gives me a synthetic index which I can use to evaluate the base instrument.  I don't technically need to save the normalized Close of the base instrument, but I do this so I can easily check the final correlation score of the sythentic index.

The image below shows a synthetic index (overlayed as the green line) on a USD chart, which is itself a synthetic index created from another repo.
![USD_H8](https://user-images.githubusercontent.com/62268115/121256188-ea23b380-c871-11eb-9052-bbaffb56f3e0.png)
