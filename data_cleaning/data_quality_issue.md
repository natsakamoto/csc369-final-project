review_date was orginally stored as an integer, so I convered it into a proper date using a cast. Then i used the review year and month from the cleaned date.

Some text columns (ex: the review itself) contained invalid UTF-8 (improper character/str encoding) so it crashed the data from my multiple parquets from being combines and cleaned. To fix it I had review_body and review_headline stored as BLOBs, but then later decoded into UTF-8 using python.

Because I converted the text columns in BLOBs I wasn't able to use str funtions (ex: TRIM()), so then I casted them as VARCHAR and then applied the functions.

After doing some exploratory analysis I found that the helpful votes are extremly skewed right. Most reviews have 0 helpful votes so I took the natural log for my EDA. 

There are also potential outliers in review length which would distort the trend, so I'm using bins and plan to cap the length at the 99th percentile.

The columns I'm using do not have any missing values (yay). 

