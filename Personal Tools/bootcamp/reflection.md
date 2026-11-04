# Part A reflection

Name: Deepak Charan S  
Student id: EE23B022
LLM provider and model used: Google Gemini, gemini-3.8-flash

<!-- 150 to 250 words. Describe one thing that went wrong or surprised you while running
bootcamp_agent.py: for example, the LLM skipped a tool, passed a wrong parameter, guessed
an answer, or recovered from an error. Point to the trace file and line that shows it,
and say what you think caused it. -->
An unexpected LLM behavior which I have observed was its decision to make two lookups for Delhi and Mumbai simultaneously, rather than processing the airports one-by-one. In `bootcamp/traces/q2.jsonl`, on line 2 at timestamp `1792385798.408`, the model had made two `lookup_node` tool calls simultaneously: one for Delhi and one for Mumbai. Once having received both results, it continued the parallel strategy by making two more calls – for incoming and outgoing degrees of both airports simultaneously. Personally, I expected the LLM to first identify Delhi and only then to proceed to Mumbai.

From my deductions, this decision of the LLM made the process of solving the problem more efficient since both airports were identified in one tool call. But it means that the LLM should be able to correctly distinguish the results related to Delhi and those related to Mumbai and then make the necessary comparison between the two numbers. When I went through this the data personally, I verified that it did everything right: Delhi has 58 incoming routes, Mumbai has 45, and the difference is 13.
