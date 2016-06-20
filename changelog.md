# Changelog

- * a903f82 - 2016-05-12: ADDED: Exception handling for socket errors during startup on tornado web server 
- * 0a6a028 - 2016-05-12: FIXED: Issue with new pip upgrades and requirements installations 
- * f202a22 - 2016-05-12: ADDED: Google API Client requirement 
- * a8568d4 - 2016-05-12: FIXED: Removed PyDrive from requirements and constraints files, using custom internal methods instead 
- * 5dd094d - 2016-05-11: UPDATES: Code added to prepare for new API server coming online shortly to link in new service features FIXED: Torrent clients having issues with username/password authentication such as uTorrent and others alike 
- * 729bfd3 - 2016-05-09: FEATURE: Google device linking 
- * b388f40 - 2016-05-08: GRUNT: Updated JS core files 
- * 020d273 - 2016-05-08: ADDED: Limit to number of shows allowed to be added at once for existing shows feature 
- * 9b0d49d - 2016-05-08: FIXED: JS Core code for root directory function FIXED: Status template code, corrected for new queue system 
- * aa47a34 - 2016-05-08: UPDATES: Javascript core components 
- * 25725c2 - 2016-05-08: FIXED: API Builder was not properly referencing help for api calls, added application and request values to template attributes 
- * 9d32ac0 - 2016-05-08: FIXED: Added space between regex names displayed via nameparser FIXED: When setting location on either show or episode it now displays a message detailing as to which location was infact set FIXED: Core JS code for mass_update and mass_edit templates was incorrectly placed resulting in certain JS features to not work correctly 
- * b5caac0 - 2016-05-08: FIXED: Expand/Collaspe button for episode status manager 
- * 082c883 - 2016-05-07: FIXED: Queue was to slow with previous shutdown implementation so added a new improved stop event 
- * 7a80c07 - 2016-05-07: FIXED: Shutdown issue caused by executor thread pools not terminating properly FIXED: Executor pools for queues are now limited to 10 tasks at a time to help with resources FIXED: Removed standard absolute regex, not very accurate 
- * e7e7340 - 2016-05-07: FIXED: Incorrect filename specified for constraints if performing a install via setup.py 
- * dedb2e8 - 2016-05-07: FIXED: Added worker queues to database mass queries and mass upserts to better handle multi-threading, also moved connection commits to transaction context and we delete threaded connection object once done with it to help solve too many open connections to the database files. 
- * ba14b9d - 2016-05-07: FIXED: References to sleep in some modules where incorrectly specified 
- * 40c8042 - 2016-05-07: UPDATED:  Changelog 
- * 6c82baf - 2016-05-07: FIXED: Disabled same-thread checks for databases to fix issues with more then one thread opening the database files FIXED: Config migrations where storing values inside class but never returning them back to config object FEATURE: Metadata providers now can optionally be enabled or disabled from post-processing config settings UPDATE: Performed grunt tasks to update js core files 
- * 553cd75 - 2016-05-06: FIXED: Issue with shutdowns and queues resolved. 
- * ef60c54 - 2016-05-06: Updated changelog 
- * 13b9977 - 2016-05-06: FIXED: Queue was not properly looping through tasks, corrected by adding a while statement FIXED: Corrupted indexer show cache files caused indexer to throw exception and fail to complete tasks 
- * 31334ab - 2016-05-05: REVAMPED: Queue system now subclasses builtin PriorityQueue to help with multi-threading and properly offload tasks to thread executor FIXED: Database transactions are now tasked by a queue system which resolves data being lost during db calls 
- * 3a69945 - 2016-05-05: FIXED: Object comparison used when trying to compare boolean against text incorrectly in provider modules, caused issues with updating cache from RSS feeds 
- * c69a161 - 2016-05-05: FIXED: Show episode file locations were not being set due to missing code runs 
- * 9e208da - 2016-05-05: FIXED: Error loading IMDb and TMDb info caused by lack of exception handling and checking of attributes 

