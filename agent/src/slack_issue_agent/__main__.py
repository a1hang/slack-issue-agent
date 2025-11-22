"""Main entry point for slack_issue_agent module.

Allows running the agent as a module: python -m slack_issue_agent.agentcore_app
This is used by Docker CMD in the AgentCore Runtime deployment.
"""

from slack_issue_agent.agentcore_app import app

if __name__ == "__main__":
    # Start HTTP server for AgentCore Runtime
    # Listens on http://0.0.0.0:8080
    # Endpoints:
    #   POST /invocations - Main agent invocation endpoint
    #   GET /ping - Health check endpoint
    app.run()
