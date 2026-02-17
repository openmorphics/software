# C++ Interface API Specification

## Overview

The EventFlow C++ interface provides low-level, high-performance bindings for neuromorphic computing applications requiring:

- Minimal latency overhead
- RAII-based memory management
- Exception safety guarantees
- Cross-platform compatibility
- Real-time execution capabilities

## Core Architecture

### Memory Management

The C++ interface follows strict RAII (Resource Acquisition Is Initialization) patterns:

```cpp
// RAII resource management
class EventFlowContext {
public:
    EventFlowContext(const Config& config);
    ~EventFlowContext(); // Cleans up all resources

    // Non-copyable, movable
    EventFlowContext(const EventFlowContext&) = delete;
    EventFlowContext& operator=(const EventFlowContext&) = delete;
    EventFlowContext(EventFlowContext&&) noexcept;
    EventFlowContext& operator=(EventFlowContext&&) noexcept;
};
```

### Exception Safety

All operations provide strong exception safety guarantees:

```cpp
// Exception-safe operations
try {
    auto model = context.load_model("model.eir");
    auto result = model->execute(inputs);
} catch (const ValidationError& e) {
    // Handle validation errors
} catch (const ExecutionError& e) {
    // Handle execution errors
} catch (const std::exception& e) {
    // Handle unexpected errors
}
```

## API Surface

### Context Management

```cpp
namespace eventflow {

// Configuration structure
struct Config {
    std::string backend = "cpu-sim";
    size_t max_memory_mb = 1024;
    bool enable_native_acceleration = true;
    LogLevel log_level = LogLevel::INFO;
    std::optional<std::string> device_id;
};

// Main context class
class Context {
public:
    explicit Context(const Config& config);
    ~Context();

    // Model management
    std::unique_ptr<Model> load_model(const std::string& eir_path);
    std::unique_ptr<Model> load_model_from_json(const nlohmann::json& eir);

    // Validation
    ValidationResult validate_eir(const std::string& eir_path);
    ValidationResult validate_eir_json(const nlohmann::json& eir);

    // Backend management
    std::vector<BackendInfo> list_backends();
    BackendInfo get_backend_info(const std::string& backend_name);

private:
    class Impl;
    std::unique_ptr<Impl> pimpl_;
};

} // namespace eventflow
```

### Model Interface

```cpp
namespace eventflow {

class Model {
public:
    virtual ~Model() = default;

    // Model metadata
    virtual std::string id() const = 0;
    virtual std::string name() const = 0;
    virtual std::string version() const = 0;
    virtual Profile profile() const = 0;

    // Execution
    virtual ExecutionResult execute(const EventTensor& inputs) = 0;
    virtual std::future<ExecutionResult> execute_async(const EventTensor& inputs) = 0;

    // Plan management
    virtual std::optional<ExecutionPlan> build_plan() = 0;
    virtual ExecutionResult execute_with_plan(const EventTensor& inputs,
                                            const ExecutionPlan& plan) = 0;

    // Capabilities
    virtual std::vector<std::string> capabilities() const = 0;
    virtual size_t max_latency_us() const = 0;
    virtual size_t memory_usage_mb() const = 0;
};

} // namespace eventflow
```

### Event Tensor Interface

```cpp
namespace eventflow {

// Event tensor representation
class EventTensor {
public:
    // Construction
    static std::unique_ptr<EventTensor> from_jsonl(const std::string& path);
    static std::unique_ptr<EventTensor> from_jsonl_stream(std::istream& stream);
    static std::unique_ptr<EventTensor> create(const TensorConfig& config);

    // Metadata access
    const Header& header() const;
    size_t size() const;
    bool empty() const;

    // Data access (zero-copy where possible)
    std::span<const EventRecord> events() const;

    // Streaming interface
    class Iterator {
    public:
        bool has_next() const;
        const EventRecord& next();
        void reset();
    };
    Iterator iterate() const;

    // Serialization
    void to_jsonl(std::ostream& output) const;
    nlohmann::json to_json() const;

private:
    class Impl;
    std::unique_ptr<Impl> pimpl_;
};

// Event record structure
struct EventRecord {
    int64_t timestamp_ns;
    std::vector<int32_t> coordinates;
    float amplitude;
    std::optional<nlohmann::json> metadata;
};

// Tensor configuration
struct TensorConfig {
    std::vector<std::string> dimensions;
    std::string time_unit = "us";
    std::string value_unit = "dimensionless";
    std::string dtype = "f32";
    std::string layout = "coo";
    std::optional<nlohmann::json> metadata;
};

} // namespace eventflow
```

### Validation Interface

```cpp
namespace eventflow {

// Validation result
struct ValidationResult {
    bool valid = false;
    std::vector<ValidationIssue> issues;

    bool has_errors() const;
    bool has_warnings() const;
    std::string summary() const;
};

// Validation issue
struct ValidationIssue {
    enum class Severity { INFO, WARNING, ERROR } severity;
    std::string code;
    std::string message;
    std::optional<Location> location;
};

// Location information
struct Location {
    std::string path;
    size_t line = 0;
    size_t column = 0;
};

// Validation functions
ValidationResult validate_eir_file(const std::string& path);
ValidationResult validate_eir_json(const nlohmann::json& eir);
ValidationResult validate_event_tensor_file(const std::string& path);
ValidationResult validate_event_tensor_json(const nlohmann::json& tensor);
ValidationResult validate_dcd_file(const std::string& path);
ValidationResult validate_dcd_json(const nlohmann::json& dcd);

} // namespace eventflow
```

### Execution Results

```cpp
namespace eventflow {

// Execution result
struct ExecutionResult {
    enum class Status { SUCCESS, FAILURE, TIMEOUT } status;
    std::optional<EventTensor> output_tensor;
    std::optional<EventTensor> trace_tensor;
    std::chrono::microseconds execution_time;
    std::optional<std::string> error_message;

    // Performance metrics
    struct Metrics {
        size_t events_processed = 0;
        double throughput_keps = 0.0;
        size_t peak_memory_mb = 0;
        size_t avg_latency_us = 0;
    };
    std::optional<Metrics> metrics;
};

// Execution plan
struct ExecutionPlan {
    std::string plan_id;
    std::string backend_name;
    std::chrono::microseconds estimated_time;
    size_t estimated_memory_mb;
    nlohmann::json plan_details;

    bool is_valid() const;
    std::chrono::system_clock::time_point expires_at() const;
};

} // namespace eventflow
```

### Streaming and Real-time Interfaces

```cpp
namespace eventflow {

// Real-time execution interface
class RealTimeExecutor {
public:
    explicit RealTimeExecutor(std::unique_ptr<Model> model);
    ~RealTimeExecutor();

    // Real-time execution
    bool execute_realtime(const EventTensor& input,
                         std::chrono::microseconds deadline);

    // Deadline management
    void set_deadline(std::chrono::microseconds deadline);
    std::chrono::microseconds current_deadline() const;

    // Performance monitoring
    struct RealtimeStats {
        size_t total_executions = 0;
        size_t deadline_misses = 0;
        std::chrono::microseconds avg_execution_time{0};
        std::chrono::microseconds max_execution_time{0};
    };
    RealtimeStats get_stats() const;
};

// Streaming interface
class StreamProcessor {
public:
    explicit StreamProcessor(std::unique_ptr<Model> model);
    ~StreamProcessor();

    // Stream processing
    void process_stream(std::unique_ptr<EventStream> input_stream,
                       std::unique_ptr<EventStream> output_stream);

    // Buffer management
    void set_buffer_size(size_t max_events);
    size_t buffer_size() const;

    // Flow control
    void pause();
    void resume();
    bool is_paused() const;
};

// Event stream interface
class EventStream {
public:
    virtual ~EventStream() = default;

    virtual bool has_data() const = 0;
    virtual std::optional<EventRecord> read_next() = 0;
    virtual bool write_record(const EventRecord& record) = 0;
    virtual void flush() = 0;
    virtual void close() = 0;
};

} // namespace eventflow
```

## Backend Integration

### Backend Interface

```cpp
namespace eventflow {

// Backend information
struct BackendInfo {
    std::string name;
    std::string type; // "cpu", "gpu", "neuromorphic"
    std::string version;
    std::vector<std::string> supported_operations;
    std::vector<Profile> supported_profiles;
    size_t max_memory_mb;
    double max_throughput_keps;
    nlohmann::json device_info;
};

// Backend capabilities
struct BackendCapabilities {
    bool supports_realtime = false;
    bool supports_async = false;
    bool supports_streaming = false;
    std::vector<std::string> supported_precisions;
    size_t max_concurrent_executions = 1;
    nlohmann::json extended_capabilities;
};

} // namespace eventflow
```

## Error Handling

### Exception Hierarchy

```cpp
namespace eventflow {

// Base exception
class EventFlowException : public std::exception {
public:
    explicit EventFlowException(const std::string& message);
    const char* what() const noexcept override;
};

// Validation errors
class ValidationError : public EventFlowException {
public:
    ValidationError(const std::string& message,
                   const std::vector<ValidationIssue>& issues);
    const std::vector<ValidationIssue>& issues() const;
};

// Execution errors
class ExecutionError : public EventFlowException {
public:
    ExecutionError(const std::string& message,
                  const std::optional<ExecutionResult>& partial_result = std::nullopt);
    const std::optional<ExecutionResult>& partial_result() const;
};

// Configuration errors
class ConfigurationError : public EventFlowException {
public:
    ConfigurationError(const std::string& message,
                      const std::string& parameter_name);
    const std::string& parameter_name() const;
};

// Resource errors
class ResourceError : public EventFlowException {
public:
    ResourceError(const std::string& message,
                 const std::string& resource_type,
                 size_t requested_amount = 0);
    const std::string& resource_type() const;
    size_t requested_amount() const;
};

} // namespace eventflow
```

## Memory Management Contracts

### Ownership Semantics

```cpp
namespace eventflow {

// RAII wrapper for external resources
template<typename T>
class Resource {
public:
    explicit Resource(T* ptr, std::function<void(T*)> deleter);
    ~Resource();

    // Access
    T* get() const;
    T* operator->() const;
    T& operator*() const;

    // Non-copyable, movable
    Resource(const Resource&) = delete;
    Resource& operator=(const Resource&) = delete;
    Resource(Resource&&) noexcept;
    Resource& operator=(Resource&&) noexcept;

private:
    T* ptr_ = nullptr;
    std::function<void(T*)> deleter_;
};

// Memory pool for high-performance allocations
class MemoryPool {
public:
    explicit MemoryPool(size_t block_size, size_t max_blocks);
    ~MemoryPool();

    void* allocate(size_t size);
    void deallocate(void* ptr);

    size_t used_memory() const;
    size_t total_memory() const;
};

} // namespace eventflow
```

## Cross-Platform Considerations

### Platform-Specific Extensions

```cpp
namespace eventflow {

// Platform detection
enum class Platform { LINUX, WINDOWS, MACOS, ANDROID, IOS };

Platform current_platform();

// Platform-specific features
#ifdef __linux__
class LinuxSpecificFeatures {
public:
    static void set_realtime_priority(int priority);
    static void pin_to_cpu_core(int core_id);
    static void enable_huge_pages();
};
#endif

#ifdef _WIN32
class WindowsSpecificFeatures {
public:
    static void set_process_priority(DWORD priority_class);
    static void enable_lock_memory_privilege();
};
#endif

// SIMD detection and utilization
class SIMDSupport {
public:
    enum class InstructionSet { NONE, SSE, AVX, AVX2, AVX512, NEON };

    static InstructionSet detect();
    static bool supports(InstructionSet set);
    static void optimize_for_instruction_set(InstructionSet set);
};

} // namespace eventflow
```

## Performance Optimizations

### Zero-Copy Operations

```cpp
namespace eventflow {

// Zero-copy tensor operations
class ZeroCopyTensor {
public:
    // Memory-mapped file support
    static std::unique_ptr<ZeroCopyTensor> from_memory_map(const std::string& path);

    // Shared memory support
    static std::unique_ptr<ZeroCopyTensor> from_shared_memory(const std::string& name);

    // Direct buffer access
    std::span<const EventRecord> data() const;
    bool is_memory_mapped() const;
    bool is_shared_memory() const;
};

// Lock-free data structures
class LockFreeQueue {
public:
    explicit LockFreeQueue(size_t capacity);
    ~LockFreeQueue();

    bool try_push(const EventRecord& record);
    bool try_pop(EventRecord& record);
    bool empty() const;
    bool full() const;
    size_t size() const;
};

} // namespace eventflow
```

## Integration Examples

### Basic Usage

```cpp
#include <eventflow/eventflow.h>
#include <iostream>

int main() {
    try {
        // Initialize context
        eventflow::Config config;
        config.backend = "cpu-sim";
        config.enable_native_acceleration = true;

        eventflow::Context context(config);

        // Load and validate model
        auto validation = context.validate_eir("model.eir");
        if (!validation.valid) {
            std::cerr << "Model validation failed\n";
            return 1;
        }

        auto model = context.load_model("model.eir");

        // Load input data
        auto input_tensor = eventflow::EventTensor::from_jsonl("input.jsonl");

        // Execute model
        auto result = model->execute(*input_tensor);

        if (result.status == eventflow::ExecutionResult::Status::SUCCESS) {
            std::cout << "Execution successful in "
                      << result.execution_time.count() << " microseconds\n";

            if (result.output_tensor) {
                result.output_tensor->to_jsonl(std::cout);
            }
        }

    } catch (const eventflow::EventFlowException& e) {
        std::cerr << "EventFlow error: " << e.what() << std::endl;
        return 1;
    } catch (const std::exception& e) {
        std::cerr << "Unexpected error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
```

### Real-Time Processing

```cpp
#include <eventflow/eventflow.h>
#include <thread>
#include <chrono>

class RealTimeProcessor {
public:
    RealTimeProcessor()
        : model_(nullptr), executor_(nullptr) {}

    bool initialize(const std::string& model_path) {
        try {
            eventflow::Config config;
            config.backend = "gpu-sim"; // Use GPU for real-time
            context_ = std::make_unique<eventflow::Context>(config);

            model_ = context_->load_model(model_path);
            executor_ = std::make_unique<eventflow::RealTimeExecutor>(std::move(model_));

            // Set 10ms deadline for real-time processing
            executor_->set_deadline(std::chrono::milliseconds(10));

            return true;
        } catch (const std::exception& e) {
            std::cerr << "Initialization failed: " << e.what() << std::endl;
            return false;
        }
    }

    bool process_frame(const eventflow::EventTensor& frame) {
        if (!executor_) return false;

        auto deadline = std::chrono::microseconds(10000); // 10ms
        return executor_->execute_realtime(frame, deadline);
    }

    void print_stats() const {
        if (executor_) {
            auto stats = executor_->get_stats();
            std::cout << "Real-time stats:\n"
                      << "  Total executions: " << stats.total_executions << "\n"
                      << "  Deadline misses: " << stats.deadline_misses << "\n"
                      << "  Average execution time: " << stats.avg_execution_time.count() << " μs\n"
                      << "  Maximum execution time: " << stats.max_execution_time.count() << " μs\n";
        }
    }

private:
    std::unique_ptr<eventflow::Context> context_;
    std::unique_ptr<eventflow::Model> model_;
    std::unique_ptr<eventflow::RealTimeExecutor> executor_;
};
```

This C++ interface specification provides a comprehensive, high-performance API for EventFlow integration in performance-critical applications while maintaining memory safety and exception safety guarantees.