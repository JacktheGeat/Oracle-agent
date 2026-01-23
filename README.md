# [AI Agent Developed at Oracle Internship](/)

This Repo contains the files and projects I made from a winter internship at Oracle. I then had a presentation that I gave where I went through a mock tech demo showcasing the AI agent I made during my time there.

The main project, what I presented at the end, was an Agent that is able to connect to Google's email and calendar API's, read unread emails, and add any appointments to the calendar and compose a reply to said emails on whether or not there is a scheduling conflict.

## How to use the Agent:
You will need a few things I do not provide:
* credentials.json: A google API service credentials. It should have access to email and calendar actions.
* .env: A environment file that contains sensitive information. I have a [sample.env](sample.env) available that contains the names of variables, though they are unset.
  * This means you will need to get an API key for cohere. this is free with rate limits.
* token.json: created automatically, this validates the google API service.

Once you have all the files and permissions allowed, You simply need to run the Agent.py file. It will look through your emails and calendar and hopefully will work without much issue.

## Thank you Mr. Wakim and Oracle:
<video src="https://jackthegeat.github.io/Email-Scheduling-AI/src/Presentation.mp4" width="640" height="480" controls></video>

The time was short, but I learned a lot about AI such as building and implementing tools, what Model Context Protocol (MCP) is and why it is important, and how to implement an Agent capable of using the tools given to it to perform complex tasks.

I started off the Internship with a crash course on how AI and Neural Networks function, and then immediately was tasked to learn and implement tools using Cohere, a free Python AI resource. 

I started off making a simple tool that allows it to get the current time based off timezone, as well as get the weather in a city.

I was then taught how to implement a local MCP server on Claude to allow it access to the tools I just made. I was then instructed to implement more complex tools, such as SQL commands in a small database, but also SQL protections, preventing access to sensitive data like passwords from reaching the AI and malicious actors.

For my final project, I made two new tools that use the gmail and google calendar API, and then created an Agent that checks unread emails for meetings or appointments, and then cross-references with my calendar for conflicts. If there are any, it will draft an email and notify me, otherwise, it will add this new event to my calendar.





