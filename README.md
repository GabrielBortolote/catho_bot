# Catho Automatic Apply

This is an automation project that can me easily installed and executed from your machine. You just need to have a python interpreter installed on your machine. I strongly recommend the usage of a virtual environment to install the dependencies listed on the *requirements.txt* file.

Just place the URLs for your saved searches inside *urls.py* file and create a file named *credentials.py* containing two variables:

- user: with your user name
- password: with the password for your Catho user

The *bot.py* script are going to import the credentials and the urls to apply for all the roles that can be applied with just one click. There are several roles that need some informations from the use to apply, this automation is going to ignore that roles, not applying for them.

The output of this script is an excel file containing data about all the jobs present on the search, you can use the outputted excel file to filter role sand apply for then using the link stored in the link column.

Enjoy it :)
