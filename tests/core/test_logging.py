from unittest.mock import MagicMock, patch

from trendscout.core.logging import log_error, request_id_ctx_var


@patch("trendscout.core.logging.logger", new_callable=MagicMock)
def test_log_error_without_request_context(mock_struct_logger):
    """Test error logging when no request context is available."""
    request_id_ctx_var.set(None)

    error = TypeError("A different test error")
    log_error(error)

    mock_struct_logger.error.assert_called_once()
    call_args = mock_struct_logger.error.call_args
    assert call_args[0][0] == "Error occurred"
    extra = call_args[1]["extra"]
    assert extra["request_id"] is None
    assert extra["error_type"] == "TypeError"
    assert extra["error_message"] == "A different test error"
    assert "method" not in extra
    assert call_args[1]["exc_info"] is True
