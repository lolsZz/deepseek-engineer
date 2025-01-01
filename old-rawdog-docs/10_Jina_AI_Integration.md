# Jina AI Integration Guide

## Overview

RAWDOG can leverage Jina AI's powerful services through MCP servers. With over 1 billion tokens available, Jina AI provides various capabilities including embeddings, classification, reranking, and document processing.

## Available Services

### 1. Embeddings Service
```typescript
// server/src/jina/embedding-service.ts
class JinaEmbeddingService {
    private apiKey: string;
    private baseUrl = 'https://api.jina.ai/v1/embeddings';

    constructor(apiKey: string) {
        this.apiKey = apiKey;
    }

    async getEmbeddings(texts: string[]) {
        const response = await fetch(this.baseUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                model: 'jina-embeddings-v3',
                task: 'text-matching',
                dimensions: 1024,
                embedding_type: 'float',
                input: texts
            })
        });

        return await response.json();
    }
}
```

### 2. Classification Service
```typescript
// server/src/jina/classifier-service.ts
class JinaClassifierService {
    private apiKey: string;
    private baseUrl = 'https://api.jina.ai/v1/classify';

    async classify(texts: string[], labels: string[]) {
        const response = await fetch(this.baseUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                model: 'jina-embeddings-v3',
                input: texts,
                labels: labels
            })
        });

        return await response.json();
    }

    async trainClassifier(trainingData: Array<{text: string, label: string}>) {
        const response = await fetch('https://api.jina.ai/v1/train', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                model: 'jina-embeddings-v3',
                access: 'private',
                num_iters: 10,
                input: trainingData
            })
        });

        return await response.json();
    }
}
```

### 3. Reranking Service
```typescript
// server/src/jina/reranker-service.ts
class JinaRerankerService {
    private apiKey: string;
    private baseUrl = 'https://api.jina.ai/v1/rerank';

    async rerank(query: string, documents: string[], topN: number = 3) {
        const response = await fetch(this.baseUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                model: 'jina-reranker-v2-base-multilingual',
                query: query,
                top_n: topN,
                documents: documents
            })
        });

        return await response.json();
    }
}
```

### 4. Document Reader Service
```typescript
// server/src/jina/reader-service.ts
class JinaReaderService {
    private apiKey: string;
    private baseUrl = 'https://r.jina.ai';

    async readUrl(url: string) {
        const response = await fetch(`${this.baseUrl}/${url}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });

        return await response.text();
    }
}
```

### 5. Text Segmentation Service
```typescript
// server/src/jina/segmenter-service.ts
class JinaSegmenterService {
    private apiKey: string;
    private baseUrl = 'https://segment.jina.ai';

    async segment(content: string, options = {
        return_tokens: true,
        return_chunks: true,
        max_chunk_length: 1000
    }) {
        const response = await fetch(this.baseUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                content,
                ...options
            })
        });

        return await response.json();
    }
}
```

## Integration with MCP Servers

### 1. Server Configuration
```yaml
# ~/.rawdog/config.yaml
mcpServers:
  jina-server:
    command: "node"
    args: ["servers/jina/build/index.js"]
    env:
      JINA_API_KEY: "jina_8465f39295ed481b8a44aeda708f1742rrhsoVYduVNpnEiZTdXcXy81L1kO"
```

### 2. Service Manager
```typescript
// server/src/jina/service-manager.ts
class JinaServiceManager {
    private services: {
        embedding: JinaEmbeddingService;
        classifier: JinaClassifierService;
        reranker: JinaRerankerService;
        reader: JinaReaderService;
        segmenter: JinaSegmenterService;
    };

    constructor(apiKey: string) {
        this.services = {
            embedding: new JinaEmbeddingService(apiKey),
            classifier: new JinaClassifierService(apiKey),
            reranker: new JinaRerankerService(apiKey),
            reader: new JinaReaderService(apiKey),
            segmenter: new JinaSegmenterService(apiKey)
        };
    }

    // Service access methods
}
```

## Use Cases

### 1. Semantic Search
```typescript
async function semanticSearch(query: string, documents: string[]) {
    // Get embeddings for query and documents
    const embeddings = await jinaServices.embedding.getEmbeddings([query, ...documents]);
    
    // Rerank results
    const reranked = await jinaServices.reranker.rerank(query, documents);
    
    return reranked;
}
```

### 2. Document Processing
```typescript
async function processDocument(url: string) {
    // Read document
    const content = await jinaServices.reader.readUrl(url);
    
    // Segment content
    const segments = await jinaServices.segmenter.segment(content);
    
    return segments;
}
```

### 3. Content Classification
```typescript
async function classifyContent(content: string[]) {
    const labels = ['technical', 'creative', 'business'];
    return await jinaServices.classifier.classify(content, labels);
}
```

## Best Practices

1. **Token Management**
   - Monitor token usage
   - Implement caching strategies
   - Use appropriate chunk sizes

2. **Error Handling**
```typescript
class JinaErrorHandler {
    static async withRetry<T>(
        operation: () => Promise<T>,
        maxRetries: number = 3
    ): Promise<T> {
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await operation();
            } catch (error) {
                if (i === maxRetries - 1) throw error;
                await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
            }
        }
        throw new Error('Max retries exceeded');
    }
}
```

3. **Performance Optimization**
```typescript
class JinaCacheManager {
    private cache = new Map<string, {
        data: any,
        timestamp: number
    }>();

    async getCached<T>(
        key: string,
        operation: () => Promise<T>,
        ttl: number = 3600000
    ): Promise<T> {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < ttl) {
            return cached.data;
        }
        
        const data = await operation();
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
        
        return data;
    }
}
```

## Security Considerations

1. **API Key Management**
```typescript
class JinaKeyManager {
    private static encryptKey(key: string): string {
        // Implement encryption
        return encrypted;
    }

    private static decryptKey(encrypted: string): string {
        // Implement decryption
        return decrypted;
    }
}
```

2. **Request Validation**
```typescript
class JinaRequestValidator {
    static validateInput(input: any): boolean {
        // Implement validation
        return isValid;
    }
}
```

## Monitoring and Logging

```typescript
class JinaMonitor {
    static logRequest(service: string, tokens: number) {
        const entry = {
            timestamp: new Date().toISOString(),
            service,
            tokens,
            remaining: /* calculate remaining tokens */
        };
        
        // Log to monitoring system
    }
}
```

## Future Considerations

1. **Enhanced Integration**
   - Automated token management
   - Advanced caching strategies
   - Performance optimizations

2. **Feature Expansion**
   - Support for new Jina AI services
   - Custom model training
   - Advanced analytics

3. **Optimization**
   - Token usage optimization
   - Response time improvements
   - Enhanced error recovery