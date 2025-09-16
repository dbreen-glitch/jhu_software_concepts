Name: Dylan Breen (dbreen1)
Module Info: Module 2 Assignment: Web Scrapping Due on 09/07/2025 at 11:59PM EST


How to run the web scrapper app:

1. Copy module_2 folder to local server.
2. Consult requirements.txt to ensure the local environment is aligned with requirements.
3. run the following code in your terminal in the copied module_2 folder
    python app.py
OPTIONAL
4. adjust the limit variable for amount of data would like to scrap and run app.py again


Approach:
Built with resources available, commit often to track changes along the process. For full approach, see commit comments as I was a bit overzealous. I built the individual functions for separate testing to see if i could get it working. I analyzed the html using "inspect" and f12 to zero in on the architecture so I could decide on the right logic. I focused on the detail page first, building out one success before moving on. I then approached crawling the survey(search) page to gather the actual result page ids. Once I had that working. I combined the two into a python file and built it out so the detail page would accept the survey ids and then join the resulting containers together. This was because the survey page held data that the detail page did not, necessitating a join. After that, I built the classes around the requirements, a bit debugging and got it to accept the data for cleaning. I can flexibly adjust the terms as needed and clean the file as I see fit. At the end, I completed the llm processing. However the outputs need more work. Ill submit now and resubmit if i get it working for less credit.

I tested at 20 and 100, was successful. I ran 50000, after 4 hours nothing so i stopped. I will do incremental test to build out the requirements. Submitting now. Need to account for timeouts, errors, and mess as that is probably slowing down or stalling my program.

During llm install, i got stuck on a few things with my wheel, but it works now. I forced an install pip install -U llama-cpp-python-cu125 so it would work with my CUDA 13.0 I think I want to try out the GPU acceleration as my laptop has the specs. This is all very informative classwork.


Known Bugs and Issues: 
Wasn't certain on the exact fields, i tried aligning them with the screenshot from the llm output, but think thats wrong. I will instead create an output for llm and a regular cleaned output. At scale appears to be stalling, needs error correction and capture for null, messy data etc. I noticed some notes are very long at higher samples sizes, so need to put a limit in for the comments as this may slow down with little quality information. Running through llm a larger dataset, they all said the university was UC Berkeley. Im glad it sees my alma mater, but sadly, that is incorrect.


Citations:
Consulted readings, Lecture recordings, Teams postings. Lecture Slides. I consulted LLM for assistance when getting stuck mid-project, but any help provided I made sure I took the time to understand what exactly was being done for further application. The mentorship resources across the board are very helpful.