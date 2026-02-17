# REST API for EventFlow

The EventFlow REST API provides HTTP-based programmatic access to neuromorphic computing capabilities for web applications, dashboards, and external integrations.

## 📋 **Status: API Specification Complete**

✅ **OpenAPI Specification**: Complete REST API design with comprehensive endpoint definitions

📁 **API Specification**: [openapi.yaml](openapi.yaml) - OpenAPI 3.0.3 specification

## 🚀 **Key Features**

- **Complete REST API**: Full coverage of EventFlow operations via HTTP
- **OpenAPI Compliant**: Standard API specification for automatic client generation
- **Authentication Ready**: JWT and API key authentication support
- **Real-Time Streaming**: WebSocket support for live event streaming
- **Rate Limiting**: Built-in request throttling and resource protection
- **Comprehensive Documentation**: Auto-generated API docs and client libraries

## 📖 **API Overview**

### Core Endpoints
- `GET /health` - System health and status monitoring
- `POST /validate/eir` - EIR document validation
- `POST /validate/event-tensor` - Event tensor validation
- `POST /models` - Model upload and management
- `POST /execute/{model_id}/run` - Synchronous and asynchronous execution
- `POST /compare/traces` - Trace conformance comparison
- `POST /sal/stream` - SAL data streaming and conversion

### Key Capabilities
- **Model Management**: Upload, list, and manage neuromorphic models
- **Execution Control**: Synchronous and asynchronous model execution
- **Validation Services**: Comprehensive validation of all EventFlow artifacts
- **Trace Analysis**: Profiling and comparison of execution traces
- **SAL Integration**: Real-time sensor data streaming
- **Backend Management**: Query and manage execution backends

## 🔧 **Integration Status**

| Component | Status | Documentation |
|-----------|--------|---------------|
| OpenAPI Specification | ✅ Complete | [openapi.yaml](openapi.yaml) |
| REST Server Implementation | ✅ Started | [server/](server/) |
| Authentication Framework | ✅ Designed | [openapi.yaml](openapi.yaml) |
| Rate Limiting | ✅ Designed | [openapi.yaml](openapi.yaml) |
| WebSocket Streaming | ✅ Designed | [openapi.yaml](openapi.yaml) |
| Client Libraries | ❌ Pending | Planned for v0.2 |
| Documentation Generation | ❌ Pending | Planned for v0.2 |

## 🎯 **Usage Example**

```bash
# Install and run the server
cd interfaces/rest/server
pip install -e .
python main.py

# Health check
curl http://localhost:8000/health

# Validate EIR model
curl -X POST http://localhost:8000/validate/eir \
  -H "Content-Type: application/json" \
  -d @model.eir

# Execute model
curl -X POST http://localhost:8000/execute/my-model/run \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": [{
      "uri": "data:input.jsonl",
      "format": "jsonl"
    }]
  }'
```

## 🚀 **Quick Start**

The REST API server is implemented in [server/](server/) using FastAPI:

```bash
cd interfaces/rest/server
pip install -e .
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## 📋 **Implementation Roadmap**

- **Phase 1** (Current): OpenAPI specification and API design
- **Phase 2** (v0.2): FastAPI implementation with authentication
- **Phase 3** (v0.3): WebSocket streaming and advanced features
- **Phase 4** (v0.4): Production deployment and scaling

## 🔗 **Related Interfaces**

- [gRPC/RPC](../rpc/) - High-performance service-to-service communication
- [C++ Interface](../cxx/) - Low-level performance bindings
- [Python SDK](../../python/) - Python client library
