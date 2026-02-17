# gRPC/RPC Interface for EventFlow

The EventFlow gRPC interface provides high-performance, strongly-typed service-to-service communication for distributed neuromorphic computing applications.

## 📋 **Status: API Specification Complete**

✅ **Protocol Buffers**: Complete gRPC service definitions with comprehensive message schemas

📁 **Protobuf Definition**: [eventflow.proto](eventflow.proto) - Complete protobuf specification

## 🚀 **Key Features**

- **High Performance**: Binary protocol with minimal serialization overhead
- **Strong Typing**: Protocol buffer definitions ensure type safety
- **Streaming Support**: Bi-directional streaming for real-time event processing
- **Load Balancing**: Built-in support for client-side and server-side load balancing
- **Authentication**: Integrated authentication and authorization
- **Multi-Language**: Automatic client generation for 10+ programming languages

## 📖 **Service Overview**

### Core Services
- **ValidationService** - Schema validation for all EventFlow artifacts
- **ModelService** - Model management and lifecycle operations
- **ExecutionService** - Synchronous and asynchronous model execution
- **TraceService** - Trace analysis and conformance comparison
- **SALService** - Real-time sensor data streaming
- **BackendService** - Backend discovery and capability queries
- **HealthService** - System health monitoring and status
- **EventStreamingService** - Real-time event streaming for live applications

### Key Capabilities
- **Streaming Execution**: Real-time model execution with event streaming
- **Asynchronous Operations**: Non-blocking execution with job status tracking
- **Trace Comparison**: High-performance trace analysis and validation
- **Multi-Format Support**: JSON, JSONL, and binary event tensor handling
- **Service Discovery**: Dynamic backend and service discovery

## 🔧 **Integration Status**

| Component | Status | Documentation |
|-----------|--------|---------------|
| Protobuf Definitions | ✅ Complete | [eventflow.proto](eventflow.proto) |
| Service Design | ✅ Complete | [eventflow.proto](eventflow.proto) |
| Streaming Support | ✅ Complete | [eventflow.proto](eventflow.proto) |
| Authentication | ✅ Designed | [eventflow.proto](eventflow.proto) |
| gRPC Server Implementation | ❌ Pending | Planned for v0.2 |
| Client Libraries | ❌ Pending | Auto-generated from protobuf |
| Load Balancing | ❌ Pending | Planned for v0.2 |

## 🎯 **Usage Example**

```python
import grpc
import eventflow_pb2 as ef
import eventflow_pb2_grpc as ef_grpc

# Create channel and stub
channel = grpc.insecure_channel('localhost:50051')
stub = ef_grpc.ExecutionServiceStub(channel)

# Execute model
request = ef.ExecuteRequest(
    model_id='my-model',
    backend='cpu-sim',
    inputs=[
        ef.InputData(
            uri='data:input.jsonl',
            format='jsonl'
        )
    ]
)

response = stub.Execute(request)
print(f"Execution status: {response.status}")
```

## 📋 **Implementation Roadmap**

- **Phase 1** (Current): Protocol buffer definitions and service design
- **Phase 2** (v0.2): Python gRPC server implementation
- **Phase 3** (v0.3): Streaming support and advanced features
- **Phase 4** (v0.4): Multi-language client libraries and production hardening

## 🔗 **Related Interfaces**

- [REST API](../rest/) - HTTP-based web service interface
- [C++ Interface](../cxx/) - Low-level performance bindings
- [Python SDK](../../python/) - Python client library
