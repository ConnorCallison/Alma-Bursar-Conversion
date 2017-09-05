[![N|Solid](https://brand.humboldt.edu/sites/default/files/styles/panopoly_image_original/public/general/hsu-mark-stacked_0.png?itok=jnMrPDcd)](http://its.humboldt.edu/)
# Alma-Bursar Data Conversion Script

This data conversion script allows for an XML file export to be converted into PeopleSoft ready .dat files and .csv for accounts receivable.

## Process overview:
  - Alma runs bursar export and delivers file via SFTP.
  - Data Conversion script is ran on delivered XML file.
  - File is delivered to functional users in Student Financial Services via shared network drive.
  - Functional users utilize PeopleSoft external file upload to load in data.

# Requirements:
  - Python 2.7
  - Python Libraries: `lxml, csv, time, os, shutil, smtplib` 
  - SFTP server

# Setup:
  - Download the Data Conversion Script.
  - Open the script in your favorite editor and:
    - Change email addresses where `humboldt.edu` is present.
    - Change SMTP server hostname.
    - (View Script Edits in Screenshot section below)
  - Identify the server that will be receiving the XML file from Alma.
  - On this server, create a user: `alma`
  - In this user's home directory, create the following folder structure:
    - `cd ~alma`
    - `mkdir bursar -m 755`
    - `cd bursar`
    - `mkdir old_xml`
    - `mkdir output`
    - `mkdir output/old`
  - Place Data Conversion Script in `/home/alma/bursar`
  - Configure the Alma Bursar export to deliver the file to `/home/alma/bursar` (see last image in Bursar Export Settings below)
  - Schedule both the Bursar export (in Alma) and the data conversion script (cron job) ten minutes apart.
  - Below you will find screenshots of our alma configuration.
  
# Screenshots:

##### Script edits:
![alt text](https://i.imgur.com/bTY48Qa.png)

##### Bursar Export Settings:

![alt text](https://i.imgur.com/st0EP2M.png)
![alt text](https://i.imgur.com/X4YBkFX.png)
![alt text](https://i.imgur.com/TPkCwCe.png)
![alt text](https://i.imgur.com/IIOWRYx.png)
![alt text](https://i.imgur.com/AW7O3cp.jpg)

##### Server configuration:
![alt text](https://i.imgur.com/4fKZn44.png)

## Contact:
 - Connor Callison
   - Available via email / Google Hangouts. 
   - connor@humboldt.edu