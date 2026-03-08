import logging
import json
import os
import time
from flask import Flask, request, g


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record),
        }
        
        request_id = getattr(record, 'request_id', None)
        if request_id is not None:
            log_data['request_id'] = request_id
        
        module = getattr(record, 'module', None)
        if module is not None:
            log_data['module'] = module
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(app: Flask | None = None) -> None:
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, log_level, logging.INFO)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    formatter = JSONFormatter()
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    
    if app:
        setup_request_logging(app)


def setup_request_logging(app: Flask) -> None:
    logger = logging.getLogger(__name__)
    
    @app.before_request
    def before_request() -> None:
        g.start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID', 'unknown')
    
    @app.after_request
    def after_request(response):  # type: ignore
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            request_id = getattr(g, 'request_id', 'unknown')
            
            logger.info(
                f"{request.method} {request.path} - {response.status_code} - {round(elapsed * 1000, 2)}ms",
                extra={
                    'request_id': request_id,
                    'module': 'request_logging'
                }
            )
        
        return response
