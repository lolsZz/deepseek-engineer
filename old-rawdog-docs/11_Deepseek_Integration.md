# Deepseek Integration Guide

## Overview

RAWDOG can leverage Deepseek's powerful models through litellm integration. This document details how to configure and use Deepseek's models in MCP servers, with particular focus on the chat and coder models.

## Configuration

### 1. Environment Setup
```yaml
# ~/.rawdog/config.yaml
mcpServers:
  deepseek-server:
    command: "node"
    args: ["servers/deepseek/build/index.js"]
    env:
      DEEPSEEK_API_KEY: "your-api-key"
      LLM_PROVIDER: "deepseek"
```

### 2. Server Implementation

```typescript
// server/src/deepseek/client.ts
import { completion } from 'litellm';

class DeepseekClient {
    private apiKey: string;

    constructor() {
        this.apiKey = process.env.DEEPSEEK_API_KEY;
        if (!this.apiKey) {
            throw new Error('DEEPSEEK_API_KEY environment variable is required');
        }
    }

    async chat(messages: any[], stream: boolean = false) {
        return await completion({
            model: "deepseek/deepseek-chat",
            messages,
            stream
        });
    }

    async code(messages: any[], stream: boolean = false) {
        return await completion({
            model: "deepseek/deepseek-coder",
            messages,
            stream
        });
    }
}
```

## Model Usage

### 1. Chat Model

```typescript
// server/src/deepseek/chat-service.ts
class DeepseekChatService {
    private client: DeepseekClient;

    constructor() {
        this.client = new DeepseekClient();
    }

    async generateResponse(prompt: string) {
        const messages = [{
            role: "user",
            content: prompt
        }];

        return await this.client.chat(messages);
    }

    async streamResponse(prompt: string) {
        const messages = [{
            role: "user",
            content: prompt
        }];

        const stream = await this.client.chat(messages, true);
        return stream;
    }
}
```

### 2. Coder Model

```typescript
// server/src/deepseek/coder-service.ts
class DeepseekCoderService {
    private client: DeepseekClient;

    constructor() {
        this.client = new DeepseekClient();
    }

    async generateCode(prompt: string) {
        const messages = [{
            role: "user",
            content: prompt
        }];

        return await this.client.code(messages);
    }

    async streamCodeGeneration(prompt: string) {
        const messages = [{
            role: "user",
            content: prompt
        }];

        const stream = await this.client.code(messages, true);
        return stream;
    }
}
```

## Integration Examples

### 1. Code Generation Server

```typescript
// server/src/deepseek/code-generation-server.ts
import { Server } from '@modelcontextprotocol/sdk/server';
import { DeepseekCoderService } from './coder-service';

class CodeGenerationServer {
    private server: Server;
    private coderService: DeepseekCoderService;

    constructor() {
        this.server = new Server({
            name: 'deepseek-code-server',
            version: '1.0.0'
        });

        this.coderService = new DeepseekCoderService();
        this.setupHandlers();
    }

    private setupHandlers() {
        this.server.setRequestHandler(
            'generate_code',
            async (request) => {
                const { prompt } = request.params;
                return await this.coderService.generateCode(prompt);
            }
        );
    }
}
```

### 2. Chat Assistant Server

```typescript
// server/src/deepseek/chat-server.ts
import { Server } from '@modelcontextprotocol/sdk/server';
import { DeepseekChatService } from './chat-service';

class ChatAssistantServer {
    private server: Server;
    private chatService: DeepseekChatService;

    constructor() {
        this.server = new Server({
            name: 'deepseek-chat-server',
            version: '1.0.0'
        });

        this.chatService = new DeepseekChatService();
        this.setupHandlers();
    }

    private setupHandlers() {
        this.server.setRequestHandler(
            'chat',
            async (request) => {
                const { message } = request.params;
                return await this.chatService.generateResponse(message);
            }
        );
    }
}
```

## Stream Processing

### 1. Stream Handler

```typescript
// server/src/deepseek/stream-handler.ts
class StreamHandler {
    static async processStream(stream: any) {
        const chunks = [];
        
        for await (const chunk of stream) {
            chunks.push(chunk.choices[0].delta.content);
            // Process chunk as needed
        }
        
        return chunks.join('');
    }
}
```

## Citation-Based Q&A

### 1. Help Center Q&A

```typescript
// server/src/deepseek/qa-service.ts
interface Article {
    id: string;
    title: string;
    content: string;
}

class QAService {
    private articles: Article[];
    private client: DeepseekClient;

    constructor(articles: Article[]) {
        this.articles = articles;
        this.client = new DeepseekClient();
    }

    async answerQuestion(question: string) {
        const prompt = `
        Articles:
        ${this.formatArticles()}

        Question: ${question}

        Answer using only information from the articles.
        Include citations as [Article ID].
        `;

        return await this.client.chat([{
            role: "user",
            content: prompt
        }]);
    }

    private formatArticles(): string {
        return this.articles.map(article => `
            [${article.id}] ${article.title}
            ${article.content}
        `).join('\n\n');
    }
}
```

### 2. Document Q&A with Quotes

```typescript
// server/src/deepseek/document-qa.ts
interface Citation {
    id: number;
    quote: string;
    context: string;
}

class DocumentQA {
    private document: string;
    private client: DeepseekClient;

    constructor(document: string) {
        this.document = document;
        this.client = new DeepseekClient();
    }

    async answerWithQuotes(question: string) {
        const prompt = `
        Document:
        ${this.document}

        Question: ${question}

        Provide answer with relevant quotes as citations.
        Format:
        <citations>
        [
            {
                "id": 1,
                "quote": "exact text from document",
                "context": "brief context"
            }
        ]
        </citations>

        <answer>
        Your answer with citations [1].
        </answer>
        `;

        return await this.client.chat([{
            role: "user",
            content: prompt
        }]);
    }
}
```

### 3. Citation Processing

```typescript
// server/src/deepseek/citation-processor.ts
interface ProcessedCitation {
    id: string;
    url: string;
    text: string;
}

class CitationProcessor {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    processCitations(response: string): ProcessedCitation[] {
        const citations = [];
        const regex = /\[(\d+)\]/g;
        let match;

        while ((match = regex.exec(response)) !== null) {
            citations.push({
                id: match[1],
                url: `${this.baseUrl}/article/${match[1]}`,
                text: response.substring(
                    match.index - 100,
                    match.index + 100
                )
            });
        }

        return citations;
    }
}
```

### 4. Citation Evaluation

```typescript
// server/src/deepseek/citation-evaluator.ts
interface EvaluationResult {
    accuracy: number;
    coverage: number;
    relevance: number;
}

class CitationEvaluator {
    async evaluateResponse(
        response: string,
        expectedCitations: string[],
        document: string
    ): Promise<EvaluationResult> {
        // Evaluate citation accuracy
        const foundCitations = this.extractCitations(response);
        const accuracy = this.calculateAccuracy(
            foundCitations,
            expectedCitations
        );

        // Evaluate document coverage
        const coverage = this.calculateCoverage(
            foundCitations,
            document
        );

        // Evaluate citation relevance
        const relevance = await this.evaluateRelevance(
            response,
            foundCitations,
            document
        );

        return { accuracy, coverage, relevance };
    }
}
```

## Error Handling

```typescript
// server/src/deepseek/error-handler.ts
class DeepseekErrorHandler {
    static async withRetry<T>(
        operation: () => Promise<T>,
        maxRetries: number = 3
    ): Promise<T> {
        let lastError;
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await operation();
            } catch (error) {
                lastError = error;
                if (i === maxRetries - 1) break;
                
                await new Promise(resolve => 
                    setTimeout(resolve, Math.pow(2, i) * 1000)
                );
            }
        }
        
        throw lastError;
    }
}
```

## Best Practices

### 1. Model Selection
- Use `deepseek-chat` for general conversation and Q&A
- Use `deepseek-coder` for code generation
- Select appropriate model based on task complexity
- Consider streaming for long responses

### 2. Error Management
- Implement proper retry mechanisms
- Handle rate limits gracefully
- Log errors for debugging
- Validate citation formats
- Handle missing document errors

### 3. Performance
- Use streaming for long responses
- Implement caching where appropriate
- Monitor response times
- Optimize document chunking
- Batch similar requests

### 4. Citation Management
- Use consistent citation formats
- Validate citations against sources
- Include context around citations
- Enable clickable citation links
- Track citation accuracy metrics

### 5. Document Q&A
- Preprocess documents for consistency
- Implement efficient document retrieval
- Balance context window size
- Maintain document structure
- Handle multiple document types

### 6. Quality Control
- Evaluate citation accuracy
- Monitor source coverage
- Track citation patterns
- Implement citation validation
- Regular quality audits

## Monitoring

```typescript
// server/src/deepseek/monitor.ts
class DeepseekMonitor {
    static logRequest(model: string, tokens: number) {
        const entry = {
            timestamp: new Date().toISOString(),
            model,
            tokens,
            latency: /* calculate latency */
        };
        
        // Log to monitoring system
    }
}
```

## Advanced Implementation Patterns

### 1. Structured Output Handling

```python
from pydantic import BaseModel
from typing import List, Optional

class FileOperation(BaseModel):
    path: str
    content: str

class DiffEdit(BaseModel):
    path: str
    original_snippet: str
    new_snippet: str

class ModelResponse(BaseModel):
    assistant_reply: str
    files_to_create: Optional[List[FileOperation]] = None
    files_to_edit: Optional[List[DiffEdit]] = None
```

Key benefits:
- Type safety and validation
- Clear interface definition
- Predictable response structure
- Easy serialization/deserialization

### 2. Diff-Based File Editing

```python
def show_diff_preview(edits: List[DiffEdit]):
    """Display proposed changes before applying."""
    table = create_diff_table()
    for edit in edits:
        table.add_row(
            edit.path,
            edit.original_snippet,
            edit.new_snippet
        )
    display_table(table)

def apply_diff_edit(edit: DiffEdit):
    """Apply a single diff edit with validation."""
    content = read_file(edit.path)
    if edit.original_snippet in content:
        new_content = content.replace(
            edit.original_snippet,
            edit.new_snippet,
            1  # Replace only first occurrence
        )
        write_file(edit.path, new_content)
        return True
    return False
```

Benefits:
- Safe, precise code modifications
- Visual preview of changes
- User confirmation before applying
- Maintains code context

### 3. Conversation Context Management

```python
class ConversationManager:
    def __init__(self):
        self.history = []
        self.file_context = {}

    def add_file_context(self, path: str, content: str):
        """Add file content to conversation context."""
        normalized_path = normalize_path(path)
        self.history.append({
            "role": "system",
            "content": f"Content of file '{normalized_path}':\n\n{content}"
        })
        self.file_context[normalized_path] = content

    def ensure_file_in_context(self, path: str) -> bool:
        """Verify or add file to conversation context."""
        normalized_path = normalize_path(path)
        if normalized_path not in self.file_context:
            try:
                content = read_file(normalized_path)
                self.add_file_context(normalized_path, content)
                return True
            except FileNotFoundError:
                return False
        return True
```

Benefits:
- Maintains conversation history
- Tracks file context
- Prevents duplicate file loading
- Normalizes file paths

### 4. Multi-LLM Workflow Patterns

The Deepseek integration supports sophisticated multi-LLM workflows for complex tasks:

#### a. Prompt Chaining
```python
def chain(input: str, prompts: List[str]) -> str:
    """Chain multiple LLM calls sequentially, passing results between steps."""
    result = input
    for i, prompt in enumerate(prompts, 1):
        result = llm_call(f"{prompt}\nInput: {result}")
    return result
```

Example Use Case - Data Processing Pipeline:
```python
processing_steps = [
    "Extract numerical values and metrics",
    "Convert to percentages where possible",
    "Sort in descending order",
    "Format as markdown table"
]

report = "Raw performance data..."
formatted_result = chain(report, processing_steps)
```

Benefits:
- Break complex tasks into manageable steps
- Each step builds on previous results
- Clear progression of data transformation
- Easier debugging and maintenance

#### b. Parallel Processing
```python
def parallel(prompt: str, inputs: List[str], n_workers: int = 3) -> List[str]:
    """Process multiple inputs concurrently with the same prompt."""
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [
            executor.submit(llm_call, f"{prompt}\nInput: {x}")
            for x in inputs
        ]
        return [f.result() for f in futures]
```

Example Use Case - Stakeholder Analysis:
```python
stakeholders = [
    "Customers: Price sensitive, Want better tech...",
    "Employees: Job security, Need new skills...",
    "Investors: Expect growth, Want cost control..."
]

impact_results = parallel(
    "Analyze market impact for this stakeholder group",
    stakeholders
)
```

Benefits:
- Improved throughput for independent tasks
- Reduced total processing time
- Efficient resource utilization
- Scalable processing architecture

#### c. Dynamic Routing
```python
def route(input: str, routes: Dict[str, str]) -> str:
    """Route input to specialized prompt based on content."""
    selector_prompt = f"""
    Analyze input and select from: {list(routes.keys())}
    Provide selection in XML format:
    <selection>team_name</selection>
    Input: {input}
    """
    
    route_key = extract_xml(llm_call(selector_prompt), 'selection')
    return llm_call(f"{routes[route_key]}\nInput: {input}")
```

Example Use Case - Support Ticket Routing:
```python
support_routes = {
    "billing": "You are a billing specialist...",
    "technical": "You are a technical support engineer...",
    "account": "You are an account security specialist..."
}

ticket = "Can't access my account..."
response = route(ticket, support_routes)
```

Benefits:
- Intelligent task distribution
- Specialized handling per input type
- Improved response quality
- Scalable routing architecture

## Future Considerations

1. **Enhanced Integration**
   - Support for new Deepseek models
   - Advanced streaming capabilities
   - Improved error handling
   - Structured output validation

2. **Performance Optimization**
   - Response caching
   - Request batching
   - Load balancing
   - Smart context management

3. **Monitoring Improvements**
   - Detailed usage analytics
   - Performance metrics
   - Cost tracking
   - Operation auditing