The [NOAA U.S. Climate Gridded Dataset (NClimGrid)](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C00332) consists of four climate variables derived from the [Global Historical Climatology Network daily (GHCNd)](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily) dataset: maximum temperature, minimum temperature, average temperature, and precipitation. The data is provided in 1/24 degree lat/lon (nominal 5x5 kilometer) grids for the Continental United States (CONUS). 

NClimGrid data is available in monthly and daily temporal intervals, with the daily data further differentiated as "prelim" (preliminary) or "scaled". Preliminary daily data is available within approximately three days of collection. Once a calendar month of preliminary daily data has been collected, it is scaled to match the corresponding monthly value. Monthly data is available from 1895 to the present. Daily preliminary and daily scaled data is available from 1951 to the present. 

This Collection contains **Monthly** data. See the journal publication ["Improved Historical Temperature and Precipitation Time Series for U.S. Climate Divisions"](https://journals.ametsoc.org/view/journals/apme/53/5/jamc-d-13-0248.1.xml) for more information about monthly gridded data.

Users of all NClimGrid data product should be aware that [NOAA advertises](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C00332) that:
>"On an annual basis, approximately one year of 'final' NClimGrid data is submitted to replace the initially supplied 'preliminary' data for the same time period. Users should be sure to ascertain which level of data is required for their research."

The source NetCDF files are delivered to Azure as part of the [NOAA Open Data Dissemination (NODD) Program](https://www.noaa.gov/information-technology/open-data-dissemination).

*Note*: The Planetary Computer currently has STAC metadata for just the monthly collection. We'll have STAC metadata for daily data in our next release. In the meantime, you can access the daily NetCDF data directly from Blob Storage using the storage container at `https://nclimgridwesteurope.blob.core.windows.net/nclimgrid`. See https://planetarycomputer.microsoft.com/docs/concepts/data-catalog/#access-patterns for more.*
