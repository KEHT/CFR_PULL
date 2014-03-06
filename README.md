CFR_PULL
========

Processing of CFR bills

PULL 2.0 ReadMe
Processing Options
To see execution options type “pull.exe” and press <ENTER>.  Note that angle brackets “<>” indicate mandatory parameter, either a directory or a filename path. Square brackets “[]” indicate an optional parameter, such as date.  Parentheses “()” indicate a choice of parameters separated by a vertical pipe “|”.  When running using a MS Windows command line interface, substitute “.exe” for “.py”.
 
“pull.exe set”
This is the main execution option of the program that would be used 99% of the time.  It will look for an input files with today’s date in M:\Toofr directory and place output files in L:\Regtext directory.
If one or both directories do not exist an error statement below is displayed:
 
On the back end software will: 
1.	Gather necessary .SGM files from M:\Toofr directory for today’s date, concatenate them together, and save to L:\Regtext with a filename YYMMMDD (e.g. 13NOV01).
2.	Apply a series of clean-up filters, formerly known as “alpha”, to a text file from previous step.
3.	Extract <REGTEXT> clauses from the above file, enrich them with necessary attributes, including effective date, ID, etc., and save in a file named YYYYMMDD.AMD (e.g. 20131101.AMD).
4.	Apply a series of clean-up filters, formerly known as “alpha” and “omega”, to an above .AMD file.
If successful, a message would be displayed with the location of the file:
 
“pull.exe auto <from> <to> [--date=<MMDDYY>]”
This option is used when flexibility is needed, particularly processing files from previous dates or retrieved from different locations.  It allows a user to specify custom source directory (<from>), destination directory (<to>), and an optional date of the file (--date=<MMDDYY>).  When date is omitted it would default to today’s date.  Format of the date is a two-digit month, day, and year (--date=123114).  Typical command line execution string would be: 
“pull.exe auto M:\Toofr L:\Regtext --date=123113”
If there are problems with the arguments one of the following three error messages would display:
 
 
 
On the back end software will: 
1.	Gather necessary .SGM files from source directory indicated by <from> argument for either a specified or today’s date, concatenate them together, and save to a destination directory indicated by <to> argument with a filename YYMMMDD (e.g. 13NOV01).
2.	Apply a series of clean-up filters, formerly known as “alpha”, to a resulting text file.
3.	Extract <REGTEXT> clauses from above file, enrich them with necessary attributes, including effective date, ID, etc. and save it with a filename YYYYMMDD.AMD (e.g. 20131101.AMD).
4.	Apply a series of clean-up filters, formerly known as “alpha” and “omega”, to an above .AMD file.
 
If successful, a message would be displayed with the location of the file:
 
“pull.exe move <from> <to> [--date=<MMDDYY>]”
Gathers necessary .SGM files from source directory indicated by <from> argument for either a specified or today’s date, concatenate them together, and save to a destination directory indicated by <to> argument with a filename YYMMMDD (e.g. 13NOV01).
If there are problems with the arguments one of the following three error messages would display:
 
 
 
If successful, a message would be displayed with the location of the file:
 
 
 “pull.exe (-h | --help)”
Outputs full array of on-screen help:
 
“pull.exe (-v | --version)”
Displays routine version number:
 

