# netflix-queue-sorter
A Python script for choosing a movie from your Netflix DVD and Instant (My List) queues.

This sortDVDqueue.py and sortInstantqueue.py scripts are deprecated. Now use chooseMovie.py to add movies to your database and to select a movie and use removeMovie.py to remove a movie from your database after you've watched it.

chooseMovie.py is a command line interface that gives you the ability to filter your queue by up to 2 genres and the displayed results are sorted by your predicted rating on Netflix. The script also searches online streaming services and displays which services you might be able to stream the movie on, if any.

Input requires copy and pasting an html block from the netflix site into a file called queue_body.html. Please refer to the header section of chooseMovie.py for implementation details.
