# Developing This Project with Cursor

I used this project as an opportunity to learn and evaluate **Cursor**, the AI-powered code editor. I had been using GitHub Copilot with VS Code for some time and wanted to compare the experience.

Overall, I was genuinely impressed. Rather than simply asking Cursor to generate code, I wanted to see how well it could participate in an organized software development workflow.

## Development Process

My workflow was as follows:

1. I wrote the initial requirements myself.
2. I used ChatGPT to review and refine the requirements and to produce a `design.md` document containing a detailed implementation plan. I also created a minimal `README.md`.
3. After saving the project files, I asked Cursor to analyze the project.
  - I quickly learned that Cursor generally expects a dedicated *work plan* document. Instead, I instructed it to use `design.md` as the authoritative implementation plan.
  - I also discovered Cursor Rules. I created project-specific rules describing the development workflow, specifying that this project was intended to learn Cursor, requiring the use of `uv`, asking Cursor to explain implementation decisions, and defining what should be included in the completion reports after each implementation step.
4. I asked Cursor to implement the project one step at a time, reviewing every change before moving to the next step.
5. Once development was complete, I tested the application and it worked as expected.
6. Finally, I implemented several small improvements and utility features, which are documented in the project history.

## Overall Impression

This was a surprisingly enjoyable experience.

The development process was smooth, fast, and easy to follow. The biggest bottleneck was me—I deliberately took my time to understand Cursor's workflow and frequently paused to review its decisions.

With the experience I gained from this project, I believe I could complete a similar project in a single day. I am looking forward to using Cursor on future projects.

## Cost

This project cost approximately **US$10** in Cursor usage.

Although this is a relatively small project, I had expected the cost to be somewhat lower. I also exhausted the free usage very quickly and upgraded to the **Cursor Pro** subscription (approximately **CA$30 including taxes** at the time).

## What I Liked

- At the beginning, I carefully reviewed every report and every line of generated code. As my confidence in Cursor increased, my reviews became much faster, eventually focusing primarily on the implementation reports and the unit test results.
- Because I emphasized testing from the start, Cursor consistently created and maintained unit tests throughout the project.
- Cursor automatically executed the test suite after each implementation step. Early in the project, a couple of regressions were introduced, but Cursor immediately detected the failures, fixed the issues, and reran the tests before considering the step complete.
- I appreciated that simple requests such as **"Push the changes"** resulted in a sensible Git workflow, committing and pushing the appropriate files without additional instructions.

## What I Would Do Differently Next Time

If I were starting another project with Cursor, I would improve my project rules from the beginning.

- Define clear standards for docstrings and code comments, including where they should be used and the expected level of detail. I ended up adding proper documentation near the end of the project.
- Add more detailed testing guidelines, including expectations for happy-path tests, edge cases, invalid input, boundary conditions, and regression tests.
- Establish stronger rules for logging and user feedback. I prefer applications that provide detailed diagnostic information in a dedicated test or debug mode, which makes troubleshooting significantly easier.
- Experiment with specialized Cursor agents for different responsibilities (such as implementation, testing, documentation, and code review). This project was too small to fully explore that capability.

## What I Did Not Like

- Now that the project is complete, I find the resulting code somewhat more complex than I would have written myself. Developing it manually would almost certainly have taken **5 to 10 times longer**, but I suspect my implementation would have been more compact, with fewer folders, files, and functions. On the other hand, Cursor produced code that follows **Clean Code** principles, with excellent separation of responsibilities and small components that each do one thing well. It is something I always try to do, I can certainly appreciate its maintainability.
- I still found myself keeping VS Code open alongside Cursor for occasional file editing and code comparisons. Old habits die hard, I guess.

