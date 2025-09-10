# 🔧 Biome JavaScript/TypeScript Analysis Preview

This page demonstrates the Biome integration capabilities for JavaScript and TypeScript code analysis.

## ⚡ Biome Overview

[Biome](https://biomejs.dev/) is a fast formatter, linter, and more for JavaScript, TypeScript, JSX, and JSON. It provides:

- **Lightning Fast**: Written in Rust for maximum performance
- **Zero Configuration**: Works out of the box with sensible defaults
- **IDE Integration**: First-class support for VS Code and other editors
- **Comprehensive**: Handles linting, formatting, and import organization

## 📝 Example Analysis

### JavaScript Example

**Input Code:**
```javascript
let config = {
    debug: true,
    apiUrl: "https://api.example.com",
    timeout: 5000
}

function processData(data){
    if(!data) return null;
    
    const results = [];
    for(let i = 0; i < data.length; i++){
        const item = data[i];
        if(item.active){
            results.push({
                id: item.id,
                name: item.name,
                timestamp: Date.now()
            });
        }
    }
    return results;
}
```

**Biome Analysis Results:**
- **Issues Found**: 2 errors
- **Fixable Issues**: 2 auto-fixable
- **Key Issues**:
  - `let config` should be `const` (never reassigned)
  - Missing semicolons and consistent formatting
  - Spacing inconsistencies

### TypeScript Example

**Input Code:**
```typescript
interface User {
    id: number;
    name: string;
    email: string;
    active: boolean;
}

class UserService {
    private apiUrl: string;
    
    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }
    
    async getUser(id: number): Promise<User> {
        const response = await fetch(`${this.apiUrl}/users/${id}`);
        return response.json();
    }
}
```

**Biome Analysis Results:**
- **Issues Found**: 1 formatting issue
- **Fixable Issues**: 1 auto-fixable
- **Key Features**:
  - Full TypeScript syntax support
  - Interface and type checking
  - Async/await pattern recognition
  - Generic type handling

## 🛠️ MCP Server Integration

The MCP server provides these Biome-powered tools:

### `biome-check`
```json
{
  "code": "const x = 'hello';",
  "file_extension": ".js",
  "config_path": "./biome.json"
}
```

### `biome-format`  
```json
{
  "code": "const x='hello';let y='world';",
  "file_extension": ".js"
}
```

### `biome-check-ci`
```json
{
  "code": "const x = 'hello';",
  "file_extension": ".ts",
  "output_format": "github"
}
```

## 🎯 File Type Support

- **JavaScript**: `.js` files with ES6+ features
- **TypeScript**: `.ts` files with full type support  
- **JSX**: `.jsx` React components
- **TSX**: `.tsx` TypeScript React components
- **JSON**: Configuration and data files

## 📊 Quality Scoring

Biome analysis contributes to the overall project quality score:

- **Style Violations**: -2 points per issue (max -40)
- **Fixable Issues**: Weighted higher in recommendations
- **File Coverage**: Number of JS/TS files successfully analyzed
- **Mixed Projects**: Combined with Python analysis for holistic scoring

## 🚀 Performance Benefits

- **Fast Analysis**: Rust-based engine for quick feedback
- **Parallel Processing**: Multiple files analyzed concurrently
- **Incremental Updates**: Only re-analyze changed code
- **Memory Efficient**: Optimized for large codebases

This integration brings modern JavaScript/TypeScript tooling to the MCP ecosystem, enabling comprehensive analysis of mixed-language projects.