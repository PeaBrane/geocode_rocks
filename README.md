This short python script processes the data exported (in csv format) from Mountain Project, such that all the problems are grouped into boulders/crags (based on their GPS coordinate similarities).

This is for the purpose of uploading the processed data into mapping applications such as Google Maps, such that each displayed pin corresponds to a boulder/crag, with the routes/grades/stars listed as description for easier organization.

This script only requires a working Python environment with the web-scraping library beautifulsoup installed.
```
pip install beautifulsoup4
```