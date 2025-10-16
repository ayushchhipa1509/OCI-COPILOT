# CloudAgentra Agent Architecture

## Current Graph Structure

```
┌─────────────────┐
│  Memory Context │ ← Entry Point (Loads memory first)
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Supervisor    │ ← Central orchestrator & state manager
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Normalizer    │ ← Query analysis & routing
└─────────┬───────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌─────┐    ┌─────────┐
│ RAG │    │ Planner │ ← Multi-step planning support
└──┬──┘    └────┬────┘
   │            │
   │            ▼
   │    ┌─────────────┐
   │    │ Supervisor  │ ← Parameter checking
   │    └─────┬───────┘
   │          │
   │          ▼
   │    ┌─────────────┐
   │    │   Codegen    │ ← Multi-step code generation
   │    └─────┬───────┘
   │          │
   │          ▼
   │    ┌─────────────┐
   │    │   Verifier   │ ← Code validation
   │    └─────┬───────┘
   │          │
   │          ▼
   │    ┌─────────────┐
   │    │  Executor   │ ← Multi-step execution
   │    └─────┬───────┘
   │          │
   └──────────┼─────────┐
              │         │
              ▼         │
    ┌─────────────────┐ │
    │ Presentation    │ │ ← User-friendly error handling
    └─────────┬───────┘ │
              │         │
              ▼         │
    ┌─────────────────┐ │
    │ Memory Manager  │ │ ← Save memory & learning
    └─────────┬───────┘ │
              │         │
              └─────────┘
```

## Key Features

### 🧠 **Memory System**

- **Memory Context**: Loads user preferences, conversation history, and project context
- **Memory Manager**: Saves learning patterns and user preferences
- **Contextual Awareness**: Provides intelligent suggestions based on history

### 🔄 **Multi-Step Operations**

- **Multiple Bucket Creation**: "create 3 buckets with names ayush_1, ayush_2, ayush_3"
- **Sequential Execution**: Each step runs independently with error handling
- **Parameter Sharing**: Compartment ID applied to all steps

### 🛡️ **Error Handling**

- **User-Friendly Messages**: Technical errors converted to helpful guidance
- **Graceful Degradation**: Suggests alternatives when operations fail
- **Smart Fallbacks**: RAG → Planner → Error handling

### 🎯 **Smart Routing**

- **Data Fetching**: Direct to codegen (no parameter checking)
- **Deployment**: Parameter gathering → Confirmation → Execution
- **Memory Integration**: Context loading and saving at each turn

## Node Responsibilities

### **Memory Context Node**

- Loads conversation history
- Loads user preferences
- Loads project context
- Provides contextual awareness

### **Supervisor Node**

- Central state orchestrator
- Parameter gathering coordination
- Error detection and retry logic
- Memory context integration

### **Normalizer Node**

- Query intent analysis
- Executable vs non-executable classification
- RAG vs Planner routing decision

### **Planner Node**

- Multi-step plan generation
- Parameter requirement analysis
- Service-specific planning
- Template-based optimization

### **Codegen Node**

- Multi-step code generation
- Service-specific patterns
- Error correction and retry
- Code optimization

### **Executor Node**

- Multi-step execution
- Sequential step processing
- Error aggregation
- Result collection

### **Presentation Node**

- User-friendly error messages
- Technical error translation
- Alternative suggestions
- Helpful guidance

### **Memory Manager Node**

- Learning pattern storage
- User preference updates
- Conversation history management
- Contextual learning

## Flow Examples

### **Simple List Operation**

```
Memory Context → Supervisor → Normalizer → Planner → Codegen → Executor → Presentation → Memory Manager
```

### **Multiple Bucket Creation**

```
Memory Context → Supervisor → Normalizer → Planner → Supervisor (Parameter Check) → Presentation (Parameter Gathering) → Planner → Codegen (Multi-step) → Executor (Multi-step) → Presentation → Memory Manager
```

### **Error Handling**

```
Memory Context → Supervisor → Normalizer → Planner → [Error] → Presentation (User-friendly error) → Memory Manager
```

## Recent Improvements

1. **Multi-Step Support**: Added capability to create multiple buckets in single query
2. **Error Handling**: User-friendly error messages instead of technical errors
3. **Memory Integration**: Context loading and learning at each turn
4. **Smart Routing**: Only check parameters for deployment operations
5. **Parameter Gathering**: Interactive compartment selection and validation
