"""AgentCore entrypoint for Slack Issue Agent.

This module provides the entrypoint for AWS Bedrock AgentCore Runtime deployment.
It integrates Strands Agents framework to process Slack events and manage issue
collection through natural conversation.

References:
    - Strands Agents: https://strandsagents.com/latest/
    - AgentCore Deployment: https://aws.github.io/bedrock-agentcore-starter-toolkit/
"""

from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp  # type: ignore[import-not-found]
from strands import Agent

# Initialize BedrockAgentCoreApp for AgentCore Runtime integration
app = BedrockAgentCoreApp()

# Configure agent with Claude Sonnet 4.5 model
agent = Agent(
    model="anthropic.claude-sonnet-4-5-20250929-v1:0",
    system_prompt=(
        "あなたは Slack Issue Agent です。"
        "ユーザーとの自然な会話を通じて Issue 情報を収集し、"
        "Slack Canvas に整理して Trello に起票します。"
    ),
)


@app.entrypoint  # type: ignore[misc]
def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    """Process Slack event and return agent response.

    This function serves as the AgentCore Runtime entrypoint. It receives a payload
    from Lambda, extracts the user prompt, processes it through the Strands Agent,
    and returns the agent's response.

    Args:
        payload: Request payload from Lambda with keys:
            - prompt: str (user message from Slack)

    Returns:
        dict: Response with keys:
            - result: str (agent's response message)

    Note:
        - BedrockAgentCoreApp handles session management automatically
        - Agent conversation history is persisted in AgentCore Memory
    """
    # Extract user message from payload
    user_message = payload.get("prompt", "")

    # Invoke agent with user input
    result = agent(user_message)

    # Return response in expected format
    return {"result": result.message}


if __name__ == "__main__":
    # Local testing support
    # Start HTTP server at http://localhost:8080
    # POST /invocations endpoint will invoke the agent
    app.run()
