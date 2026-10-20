# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Add owner and pet info, users can add/edit tasks, generate daily schedule based on priorities and constraints

Initial UML decision was having Pet, Owner, Task, and Schedule main objects, each with their own attributes and methods. For example, Pet has attributes name, species, related Tasks, and methods to add or remove tasks. Owner: name, preferences, methods for adding/removing pets and tasks, etc for Task and Schedule.

Owner can have multiple pets, assign multiple tasks, and generate Schedule, Task can be applied to multiple pets, multiple pets can have multiple tasks, etc. 

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

AI suggested ScheduledItem as an additional object for additional clarity, which makes sense. One ScheduledItem can have a task, owner, pet, etc assigned to it.

Asked AI if it notices any missing relationships or potential logic bottlenecks. Suggested fixing how time was represented and a better Task-to-Pet link because of how the rest of the code builds on them. Time is a string, better to change that. Task cannot tell which Pet it belongs to.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

Started off in Plan mode to brainstorm the initial structure. Made refinements or suggestions as it went on and asked questions whenever needed for explanations or why the AI did something extra. 

- What kinds of prompts or questions were most helpful?

Asking the AI to explain was the biggest one. AI proposed suggestions, noticed possible problems, and asking about them helped me put into perspective the thinking of the AI and decide if its a worthwhile addition, extra, or not needed at all.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

When I asked it to analyze the UML skeleton, it proposed a number of possible issues, as part of what to ask for the project. Proposed implenting checks or fixes for all of them.

- How did you evaluate or verify what the AI suggested?

Read through them, asked questions, and decided on ones which were more important than others or some which were a bit extra for the scope of the project.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
