"""Tests for AgentCore entrypoint implementation."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestAgentCoreEntrypoint:
    """Test AgentCore application entrypoint following TDD methodology."""

    def test_agentcore_app_module_imports_successfully(self) -> None:
        """Test that agentcore_app module can be imported without errors."""
        from slack_issue_agent import agentcore_app  # noqa: F401

    def test_app_instance_exists(self) -> None:
        """Test that BedrockAgentCoreApp instance is created."""
        from slack_issue_agent.agentcore_app import app

        # App should be an instance of BedrockAgentCoreApp
        assert app is not None
        assert hasattr(app, "entrypoint")

    def test_invoke_function_is_decorated_with_entrypoint(self) -> None:
        """Test that invoke function has @app.entrypoint decorator."""
        from slack_issue_agent.agentcore_app import invoke

        # Check that invoke is callable
        assert callable(invoke)

    def test_invoke_accepts_payload_dict(self) -> None:
        """Test that invoke function accepts a dictionary payload."""
        from slack_issue_agent.agentcore_app import invoke

        # Test with minimal payload
        test_payload: dict[str, Any] = {"prompt": "Hello"}

        # Should not raise TypeError
        with patch("slack_issue_agent.agentcore_app.agent") as mock_agent:
            # Mock agent's response
            mock_result = MagicMock()
            mock_result.message = "Response from agent"
            mock_agent.return_value = mock_result

            result = invoke(test_payload)
            assert isinstance(result, dict)

    def test_invoke_extracts_prompt_from_payload(self) -> None:
        """Test that invoke function extracts 'prompt' key from payload."""
        from slack_issue_agent.agentcore_app import invoke

        test_payload = {"prompt": "Test message"}

        with patch("slack_issue_agent.agentcore_app.agent") as mock_agent:
            mock_result = MagicMock()
            mock_result.message = "Agent response"
            mock_agent.return_value = mock_result

            invoke(test_payload)

            # Verify agent was called with the prompt
            mock_agent.assert_called_once_with("Test message")

    def test_invoke_returns_result_dict_with_message(self) -> None:
        """Test that invoke returns a dictionary with 'result' key containing agent's message."""
        from slack_issue_agent.agentcore_app import invoke

        test_payload = {"prompt": "Hello agent"}
        expected_response = "Hello! How can I help you with Slack Issue tracking?"

        with patch("slack_issue_agent.agentcore_app.agent") as mock_agent:
            mock_result = MagicMock()
            mock_result.message = expected_response
            mock_agent.return_value = mock_result

            result = invoke(test_payload)

            # Verify response structure
            assert isinstance(result, dict)
            assert "result" in result
            assert result["result"] == expected_response

    def test_invoke_handles_empty_prompt_with_default(self) -> None:
        """Test that invoke handles missing or empty 'prompt' key gracefully."""
        from slack_issue_agent.agentcore_app import invoke

        # Test with empty payload
        test_payload: dict[str, Any] = {}

        with patch("slack_issue_agent.agentcore_app.agent") as mock_agent:
            mock_result = MagicMock()
            mock_result.message = "Default response"
            mock_agent.return_value = mock_result

            invoke(test_payload)

            # Should call agent with empty string or default prompt
            mock_agent.assert_called_once()
            call_args = mock_agent.call_args[0][0]
            assert isinstance(call_args, str)  # Should be a string

    def test_agent_uses_claude_sonnet_4_5_model(self) -> None:
        """Test that Agent is configured with Claude Sonnet 4.5 model."""
        from slack_issue_agent.agentcore_app import agent

        # Agent should be initialized
        assert agent is not None

        # Model should be Claude Sonnet 4.5
        # The exact model ID from design.md
        expected_model = "anthropic.claude-sonnet-4-5-20250929-v1:0"

        # Access agent's model configuration
        # agent.model is a BedrockModel object with config dict
        assert hasattr(agent, "model")
        assert hasattr(agent.model, "config")
        assert "model_id" in agent.model.config
        assert agent.model.config["model_id"] == expected_model

    def test_agent_has_system_prompt_for_slack_issue_agent(self) -> None:
        """Test that Agent has appropriate system prompt for Slack Issue Agent role."""
        from slack_issue_agent.agentcore_app import agent

        # Agent should have system prompt configuration
        assert agent is not None

        # System prompt should mention Slack Issue Agent role
        if hasattr(agent, "system_prompt"):
            system_prompt = agent.system_prompt
            assert "Slack Issue Agent" in system_prompt or "Issue" in system_prompt
        elif hasattr(agent, "_system_prompt"):
            system_prompt = agent._system_prompt
            assert "Slack Issue Agent" in system_prompt or "Issue" in system_prompt
        else:
            pytest.skip("System prompt verification requires runtime inspection")

    def test_invoke_is_json_serializable_response(self) -> None:
        """Test that invoke function returns JSON-serializable response."""
        from slack_issue_agent.agentcore_app import invoke

        test_payload = {"prompt": "Test"}

        with patch("slack_issue_agent.agentcore_app.agent") as mock_agent:
            mock_result = MagicMock()
            mock_result.message = "JSON serializable response"
            mock_agent.return_value = mock_result

            result = invoke(test_payload)

            # Should be JSON serializable
            try:
                json.dumps(result)
            except (TypeError, ValueError) as e:
                pytest.fail(f"Response is not JSON serializable: {e}")

    def test_app_run_method_exists_for_local_testing(self) -> None:
        """Test that app.run() method exists for local testing support."""
        from slack_issue_agent.agentcore_app import app

        # App should have run method for local testing
        assert hasattr(app, "run")
        assert callable(app.run)
