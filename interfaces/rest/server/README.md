# EventFlow REST API Server

FastAPI-based implementation of the EventFlow REST API specification.

## 🚀 **Quick Start**

```bash
# Install dependencies
pip install -e .

# Run development server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with automatic OpenAPI documentation at `http://localhost:8000/docs`.

## 📋 **Features**

- **FastAPI Framework**: Modern, high-performance async web framework
- **Auto-generated OpenAPI**: Interactive API documentation at `/docs`
- **Type Safety**: Full Pydantic model validation
- **CORS Support**: Configurable cross-origin resource sharing
- **Health Monitoring**: Comprehensive health check endpoints
- **Error Handling**: Structured error responses with proper HTTP status codes

## 🏗️ **Architecture**

### Core Components

- **`main.py`**: Main FastAPI application with route definitions
- **Health Service**: System monitoring and status reporting
- **Validation Service**: EIR and event tensor validation
- **Execution Service**: Synchronous and asynchronous model execution
- **Model Service**: Model management and metadata

### EventFlow Integration

The server integrates with EventFlow through lazy imports to avoid startup overhead:

```python
# Lazy loading of EventFlow modules
import eventflow_core
import eventflow_cli
```

## 🔧 **Configuration**

### Environment Variables

- `EF_NATIVE`: Enable/disable native acceleration (default: auto)
- `EVENTFLOW_BACKEND`: Default execution backend (default: cpu-sim)

### Command Line Options

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📖 **API Endpoints**

### Health & System
- `GET /health` - System health check
- `GET /` - API information

### Validation
- `POST /validate/eir` - Validate EIR documents
- `POST /validate/event-tensor` - Validate event tensors

### Model Management
- `GET /models` - List available models
- `GET /models/{model_id}` - Get model details

### Execution
- `POST /execute/{model_id}/run` - Execute model synchronously
- `POST /execute/{model_id}/run/async` - Execute model asynchronously
- `GET /jobs/{job_id}` - Get execution job status

## 🧪 **Development**

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Type checking
mypy .
```

## 📦 **Deployment**

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production

```bash
# Install production dependencies only
pip install --no-dev .

# Run with production ASGI server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🔗 **Integration**

The REST API server integrates with:

- **EventFlow Core**: Model validation and execution
- **EventFlow CLI**: Command-line interface functionality
- **EventFlow Backends**: Hardware acceleration backends

## 🤝 **Contributing**

1. Follow the existing code style and patterns
2. Add comprehensive tests for new endpoints
3. Update OpenAPI documentation
4. Ensure type hints are complete
5. Test with both EventFlow available and unavailable

## 📋 **Roadmap**

- **Phase 1** (Current): Basic FastAPI implementation with core endpoints
- **Phase 2**: Authentication and authorization
- **Phase 3**: Rate limiting and request throttling
- **Phase 4**: WebSocket streaming support
- **Phase 5**: Production deployment and monitoring