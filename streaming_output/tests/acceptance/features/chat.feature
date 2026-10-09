Feature: Chat with Local LLM
  As a user
  I want to send a prompt to the local LLM
  So that I can see the response streamed back to me

  Scenario: User opens the chat interface
    Given the chat interface is running
    When the user navigates to the root URL
    Then the user should see the chat UI

  Scenario: User sends a message
    Given the chat interface is running
    When the user submits a message "What is the capital of France?"
    Then the response should contain the user message "What is the capital of France?"
    And the response should include an SSE connection setup
