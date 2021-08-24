# jobsearch
Fetches IT jobs from "platsbanken" in my area
This is one of the first scripts I wrote on my own, is it totally clean? no.
I'm pretty sure that platsbanken already has this feature, but I wanted to try doing this on my own for some python training, I run this script myself in a cronjob twice a week.


Dependencies:
pip3 install requests pymongo

This script works by first contacting "platsbankens" (Swedish Public Employement Services webpage for job posts) API.
Then we pull the data that we need (job ID, job title, employer, if it's fulltime or not, when the post expires etc.) and format this for our MongoDB.
We then compare job IDs with the ones aldready in our database and add the jobs that do not exist both to the database and to the email that we're going to send.
Then we format the email to look a little bit nicer and add in our data from the database.
And last of all.. we clean up the database by checking for expired job posts and deleting them.
