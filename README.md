# netflix-queue-sorter
Python script to sort Netflix DVD and Instant (My List) queues

This script takes a Netflix DVD or Instant queue in the form of html and sorts it by predicted rating.

It currently returns html chunks for copying and pasting back into browser html code for updating the queue.

Future implementation (using either RoboBrowser or Selenium) will update the form automatically.

Authorization is accomplished using a cookies.txt file with from a logged in session because Netflix does not provide a stable API for such tasks.
