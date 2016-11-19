# FilmTrackr
FilmTrackr is an analysis engine bootstrapped to Flask that allows you to analyze your viewing habits for movies.
It allows you to enter a single movie-watching experience into the global list, or upload an entire list of your own,
which will be batch-added to the global file.

In either case, you are able to then look at graphical representations of your data and the global trends. This can
highlight interesting trends such as what genres you frequent (and likely enjoy more), how frequently you watch a movie
at your house vs. at the theater, and how much money you could've save by solely going to matinees/how much you've saved
already.

For uploaded lists, documents with JSON or YAML formatting are accepted. Functionality to create the list on the site
itself is forthcoming, but the format is easy enough that nothing more than notepad is required; Human readability is
the main purpose of YAML, after all. A sample is as follows:

    ---
    '1':
      Title: Blarg
      Day: 7
      Month: 11
      Year: 2007
      Theater?: n
    '2':
      Title: Revenge of Blarg
      Day: 11
      Month: 11
      Year: 2007
      Theater?: n
    '3':
      Title: A Film other than Blarg
      Day: 27
      Month: 12
      Year: 2016
      Theater?: y

...and such.

User authentication (and a user system) don't exist because *they're not needed*. Instead we generate a hash using
SHA256 using all of the data fields, and place each entry into the global list using that hash as the key and the
data fields as the values. This means that when a user uploads their list again after adding the most recent film
they've seen, no duplicates will be added. Prior recorded entries will have the same hash and be skipped over; new
entries will be added to the global record.

Problems with such: if two people see the same movie on the same day in the same environment, it's a collision in
the global database. Expected solution is to change the hash formula to also include one of the following options:

* **IPv4 Address**: Benefits include users being able to upload from more than one device within their home and maintain
continuity as observed by the server. Problems include the fact that IPv4 is on it's way out, and the fact that this
system fails when more than one user is on that specific local network.

* **IPv6 Address**: Benefits include being unique to each device, allowing multiple users per home/LAN. Problems includes
duplication of entries if someone uploads on more than one device on their network at different time periods.

* **MAC Address**: Same as above, with additional benefit of being harder to spoof through a proxy/VPN than an IP address
of either sort.

That sums up the functionality. Please report any bugs you find and feel free to send pull requests my way.
