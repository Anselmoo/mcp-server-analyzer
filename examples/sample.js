// Example JavaScript file with some issues for Biome to detect
const message = 'Hello, World!';
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

export { processData, config };