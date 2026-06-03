
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
import json
from dotenv import load_dotenv
from utils.config import AWS_REGION, LLM_MODEL_ID, LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TOP_P

load_dotenv()

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def call_llm(prompt, system_prompt=None):
    """
    Calls AWS Bedrock LLM (Amazon Nova Micro).

    Args:
        prompt        : User message / main prompt
        system_prompt : System instructions (optional)

    Returns:
        LLM response as string
    """
    body = {
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ],
        "inferenceConfig": {
            "maxTokens": LLM_MAX_TOKENS,
            "temperature": LLM_TEMPERATURE,
            "topP": LLM_TOP_P,
        },
    }

    if system_prompt:
        body["system"] = [{"text": system_prompt}]

    response = bedrock.invoke_model(
        modelId=LLM_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )

    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"]


if __name__ == "__main__":
    response = call_llm("Say hello in 10 words or less.")
    print(f"LLM Response: {response}")
    print("Bedrock LLM connected successfully!")
