## Web app on python
That is a web app on Python for monitoring your finances. It was a problem to solve. I have received templates and specifications, so I have to realize it.

### The functions that were implemented and tested:

* registering a new user and verifying that their portfolio page loads with the correct information,
* requesting a quote using a valid stock symbol,
* purchasing one stock multiple times, verifying that the portfolio displays correct totals,
* selling all or some of a stock, again verifying the portfolio, and
* verifying that your history page shows all transactions for your logged-in user.

### Also was implemented and tested protection against unexpected usage, as by:

* inputting alphabetical strings into forms when only numbers are expected,
* inputting zero or negative numbers into forms when only positive numbers are expected,
* inputting floating-point values into forms when only integers are expected,
* trying to spend more cash than a user has,
* trying to sell more shares than a user has,
* inputting an invalid stock symbol, and
* including potentially dangerous characters like ' and ; in SQL queries.
