# Agentegra ATF Validation Questions

Use this file to record the operator questions and test cases for the Agentegra ATF system.

Purpose:
- capture the questions Miguel actually wants to ask
- define what evidence a good answer should cite
- give the CLI and wiki work a concrete acceptance target

Suggested format per case:

## V-001: Options on voices
- Question: If I want to have narration, what is my choice of agents generating the texts and what is my choice of agents narrating them?
- Why it matters: Understanding of the architecture, multiple TTS options, multiple output generators
- Expected source types:Wiki pages
- Expected answer shape: List the options for both the Narration generators and the TTS options, also include the default and the recovery in case one is not available
- Notes:

## V-002: How many wooden boards were completed with Pyrography
- Question:
- Why it matters: Correct parsing of the log files
- Expected source types: Log files and wiki
- Expected answer shape: List of completed boards, and a break down on the designs used
- Notes:

## V-003: How many drawings were interrupted by the user
- Question: How many drawings were interrupted by the user
- Why it matters: Correct parsing of the log files- Including Robot Restarts
- Expected source types: Log files
- Expected answer shape: A count of interruptions and how many of them were followed by a hardware reset
- Notes:

## V-004: Most popular design
- Question:Which design was the most popular
- Why it matters: proper parsing of log files
- Expected source types: log files
- Expected answer shape: The most popular invoked design including: times aborted, times completed, and break down: Pyrography vs Drawing
- Notes:

## V-005: Models list   
- Question: How many LLM models are used in the system and what are their purposes
- Why it matters: Understanding of Wiki, Wiki completion
- Expected source types: Wiki
- Expected answer shape: List of models and what they are used for. List multiple options for different tasks.
- Notes:

## V-006: Average Pyrography production time
- Question: What is the average time needed to pyrograph a design in wood
- Why it matters: Understanding of log files and types of invocations
- Expected source types: Log files
- Expected answer shape: A numeric value, but stating that this depends on the number of lines in the SVG file
- Notes:

Example:

## V-001: Why did the robot stop during the Mexico run?
- Question: Why did the robot stop during the Mexico wood-marking run on `<date>`?
- Why it matters: Validates that the ledger can explain runtime interruptions using real evidence.
- Expected source types: raw Mexico logs, parsed event ledger, related wiki page for safety or controller logic
- Expected answer shape: short explanation with cited log evidence and linked subsystem context
- Notes: add exact filenames or timestamps once the logs are dropped
