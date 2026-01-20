# [AI Agent Developed at Oracle Internship](/)

This Repo contains the files and projects I made from a winter internship at Oracle. I then had a presentation that I gave where I went through a mock tech demo showcasing the AI agent I made during my time there.

[Tech demo recording](/Presentation.mp4)

The time was short, but I learned a lot about AI such as building and implementing tools, what Model Context Protocol (MCP) is and why it is important, and how to implement an Agent capable of using the tools given to it to perform complex tasks.

I started off the Internship with a crash course on how AI and Neural Networks function, and then immediately was tasked to learn and implement tools using Cohere, a free Python AI resource. 

I started off making a simple tool that allows it to get the current time based off timezone, as well as get the weather in a city.

I was then taught how to implement a local MCP server on Claude to allow it access to the tools I just made. I was then instructed to implement more complex tools, such as SQL commands in a small database, but also SQL protections, preventing access to sensitive data like passwords from reaching the AI and malicious actors.

For my final project, I made two new tools that use the gmail and google calendar API, and then created an Agent that checks unread emails for meetings or appointments, and then cross-references with my calendar for conflicts. If there are any, it will draft an email and notify me, otherwise, it will add this new event to my calendar.