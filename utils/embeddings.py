import boto3
import json
from dotenv import load_dotenv

load_dotenv()

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

def get_embedding_function():
    def embed(texts):
        embeddings = []
        for text in texts:
            response = bedrock.invoke_model(
                modelId="amazon.titan-embed-text-v2:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({"inputText": text}),
            )
            result = json.loads(response["body"].read())
            embeddings.append(result["embedding"])
        return embeddings
    return embed

if __name__ == "__main__":
    embed = get_embedding_function()
    test = embed(["Hello Manali"])
    print(f"Embedding dimension: {len(test[0])}")
    print("Bedrock Titan Embeddings working!")