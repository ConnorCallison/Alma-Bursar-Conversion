[![N|Solid](https://brand.humboldt.edu/sites/default/files/styles/panopoly_image_original/public/general/hsu-mark-stacked_0.png?itok=jnMrPDcd)](http://its.humboldt.edu/)
# Alma-Bursar Data Converison Script

This data converison script allows for an XML file export to be converted into PeopleSoft ready .dat files and .csv for accounts revieveable.

## Process overview:
  - Alma runs bursar export and delivers file via SFTP.
  - Data Conversion script is ran on delivered XML file.
  - File is delivered to functional users in Student Financial Services via shared network drive.
  - Functional users utilize peoplesoft external file upload to load in data.

# Requirements:
  - Python 2.7
  - Python Libraries: `lxml, csv, time, os, shutil, smtplib` 
  - SFTP server

# Setup:
  - Download the Data Conversion Script.
  - Identify the server that will be receiving the XML file from Alma.
  - On this server, create a user: `alma`
  - In this user's home directory, create a folder `bursar`.
  - Place Data Conversion Script in `/home/alma/bursar`
  - Configure the Alma Bursar export to deliver the file to `/home/alma/bursar`
  - Schedule both the Bursar export (in Alma) and the data conversion script (cron job) ten minutes apart.
  - Export documents as Markdown, HTML and PDF
