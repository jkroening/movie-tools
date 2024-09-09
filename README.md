# Netflix Queue Sorter
A Python script for choosing a movie from your Netflix DVD and Instant (My List) queues.

This sortDVDqueue.py and sortInstantqueue.py scripts are deprecated. Now use chooseMovie.py to add movies to your database and to select a movie and use removeMovie.py to remove a movie from your database after you've watched it.

chooseMovie.py is a command line interface that gives you the ability to filter your queue by up to 2 genres and the displayed results are sorted by your predicted rating on Netflix, displaying on which streaming services the movie might be available.

addMovies.py processes your Netflix queue (by reading input HTML files you create) and adds those movies to your database with their streaming availability across multiple services: Netflix, Hulu Plus, Amazon Prime, Crackle, Epix, ...

removeMovie.py removes a specified movie from your JSON database. (You'll probably want to do this once you watch it.)

Input requires copy and pasting an html block from the netflix site into a file called queue_body.html. Please refer to the header section of chooseMovie.py for implementation details.

Other requirements include:
  - a configuration file located in config/config.csv containing an API key for The Movie Database (see config/config_EXAMPLE.csv)
  - a JSON database skeleton with schema as laid out in databases/movies_db_EXAMPLE.json
  - input HTML files for your DVD queue, Saved Movies queue, and My List (streaming queue) -- see comments in addMovies.py

# whatToWatch
A Python script that will combine Letterboxd and Movielens to create a csv of your top predicted movies to watch next. You feed the script an html from Letterboxd of your top predicted movies (and available to stream if you so choose) -- it assumes the structure comes from your Watchlist page. You also feed the script a txt file that is the copy-pasted films from your top movies from Movielens. It will then cross-reference the lists to provide a csv of the overlapping films, that can be uploaded to a Letterboxd list.

# siftJustWatch
A Python script that will search JustWatch for a movie, based on a command line prompt.