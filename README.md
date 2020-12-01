# Poll Up: Your All-in-One Polling System

## About

Current internet polling services like Strawpoll and Facebook’s built-in polling feature don’t allow voting for multiple
options, and if they do, they don’t allow a ranking of your voting choices. This means that the winner of the poll is
decided by whichever option got the most votes. This is called plurality voting, and it’s a bad voting system because
it’s susceptible to vote-splitting and does not satisfy the Condorcet criterion.

There are several other voting systems, such as instant-runoff voting and ranked pairs, each with their own pros and
cons. This API is similar to Strawpoll, where users can create polls and share the link with their friends. However,
our solution would allow the creator of the poll to specify the voting system they would like to use. Those receiving
the poll will see which voting system is being used, along with a brief explanation of how the chosen voting system
works. These polls can be used in various scenarios such as deciding on a restaurant between friends or voting on
officers for a student-led club.

## How to Execute Our Program

### Creating a Manual Run on your Local Machine:

Clone our repository:

```git clone https://github.com/paekman17/Poll_Up_COEN174_Project_ver2 ```

Create a virtual environment (if you don't have one already):

```python3 -m venv env```

Activate the environment:

```source env/bin/activate```

Install all of the required Python libraries:

```pip install -r requirements.txt```

Set the Flask app to poll_up.py

```export FLASK_APP=poll_up.py```

Run the API:

```flask run ```
