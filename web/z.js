// const { PromptTemplate } = require('@langchain/core/prompts');

// const query = 'Tell me a joke';
// const prompt = PromptTemplate.fromTemplate(query);

// // If you are allowing more than one language model input connection (-1 or
// // anything greater than 1), getInputConnectionData returns an array, so you
// // will have to change the code below it to deal with that. For example, use
// // llm[0] in the chain definition

// const llm = await this.getInputConnectionData('ai_languageModel', 0);
// let chain = prompt.pipe(llm);
// const output = await chain.invoke();
// return [ {json: { output } } ];


const { QdrantClient } = require('/home/node/node_modules/@qdrant/js-client-rest');
const fetch = require('node-fetch');
const { CohereRerank } = require("@langchain/cohere");
const { DynamicTool } = require("@langchain/core/tools");

// 1. Tool Config
const name = 'bitcoin_whitepaper_tool';
const description = 'Call this tool to get information and/or context from the Bitcoin Whitepaper';

// 2. Qdrant config
const client = new QdrantClient({ url: 'http://qdrant:6333' });
const collectionName = 'sparse_vectors_example';
const limit = 20;

// 3. Cohere config
const cohereRerank = new CohereRerank({
  apiKey: '<MY_COHERE_API_KEY>', // Default
  model: "rerank-english-v3.0", // Default
});

// 4. Inputs
const inputData = await this.getInputData();
const embeddings = await this.getInputConnectionData('ai_embedding', 0);
const sparseVectorTool = await this.getInputConnectionData('ai_tool', 0);

// 5. Execute
const query = inputData[0].json.query;

const denseVector = await embeddings.embedQuery(query);
const sparseVector = JSON.parse(await sparseVectorTool.invoke(query));

const response = await client.query(collectionName, {
  prefetch: [
    {
      query: denseVector,
      using: 'default',
      limit: 100
    },
    {
      query: sparseVector,
      using: 'bm42',
      limit: 100
    }
 ],
 query: { fusion: 'rrf' },
 with_payload: true,
 limit: 20
});

const docs = response.points.map(res => ({
  pageContent: res.payload.content,
  metadata: res.payload.metadata
}));
const rankings = await cohereRerank.rerank(docs, query);
rankings.forEach(rank => { docs[rank.index].score = rank.relevanceScore });

const rankedDocs = docs.toSorted((a,b) => b.score-a.score);
return rankedDocs;