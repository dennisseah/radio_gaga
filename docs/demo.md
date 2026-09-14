# Demonstration

This section provides a demonstration of the features and capabilities of the
project.

## Example Usage

Here is an example of how to use the project in a typical scenario.

1. User enters the required input into the system.
2. The input is sent to LLM for response generation.
3. The system receives the generated response from LLM.
4. The response is displayed to the user.
5. We also provide the latency and token usage information for each request.

## Notes

1. We have two ways of compacting the chat history. The first method is based on
   the sum of tokens in the conversation. When the total number of tokens
   exceeds a certain threshold, summarization is performed to reduce the number
   of tokens while retaining the essential information.
2. The second method is based on the number of turns in the conversation. When
   the number of turns exceeds a certain limit, summarization is performed to
   reduce the number of turns while retaining the essential information.
3. Both methods aim to maintain the efficiency and relevance of the conversation
   by reducing unnecessary information while preserving the core context.
4. Once the session ends, the chat history is stored in a file for future
   reference. In production environments, it shall be stored in a data store
   like Cosmos DB or any other suitable database.
5. Once a new session begins, the previous chat history is loaded from the
   storage to provide continuity and context for the conversation.
6. Instructions are added to the system prompt to avoid jailbreak and
   prompt-injection attempts, ensuring that the system follows the intended
   safety and operational guidelines.
