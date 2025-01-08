from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from config import config
import json
from model import model

system_prompt = """
You are a precise content analyzer specialized in extracting place information from social media content. Follow these instructions exactly:

1. ANALYSIS RULES:
   - Only extract places that are EXPLICITLY mentioned
   - Never infer or guess places that aren't clearly stated
   - If no places are mentioned, set contentPlaces to false
   - Maintain exact spelling and formatting of place names
   - Only use information from the provided content

2. PLACE IDENTIFICATION:
   - A valid place must be a physical location that people can visit
   - Must fit one of the specified categories
   - Must be mentioned by name
   - General references like "the restaurant" without a name are not valid places


3. QUALITY CHECKS:
   - Verify each place matches a valid category
   - Ensure all required fields are filled
   - Double-check that extracted places are actually mentioned in the content
   - Confirm tags are based on explicit mentions
"""

user_prompt = lambda caption, transcript, text_detected: f"""
Analyze the following content for place information:

CAPTION:
{caption}

TRANSCRIPT:
{transcript}

TEXT DETECTION:
{text_detected}

Extract all explicitly mentioned places following the system rules. 
If no valid places are found, set contentPlaces to false and return an empty results array.
"""


def parse_output(json_data: dict) -> model.ResponseModel:
    try:
        caption = json_data.get('caption')
        text_detected = json_data.get('text_detected')
        transcript = json_data.get('transcript')
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt,
                ),
                ("human", "{query}"),
            ]
        )

        llm = ChatOpenAI(
            model="gpt-4o", 
            temperature=0.1,
            top_p=0.2,
            api_key=config.OPEN_ROUTER_API, 
            base_url='https://openrouter.ai/api/v1'
        )
        llm_with_tools = llm.bind_tools([model.ResponseModel])
        chain = prompt | llm_with_tools
        query =  user_prompt(caption, transcript, text_detected)
        response = chain.invoke({"query": query})
        json_data = json.loads(response.model_dump_json())
        json_data = json.loads(json_data['additional_kwargs']['tool_calls'][0]['function']['arguments'])
        return model.ResponseModel(**json_data)
    except Exception as e:
        return model.ResponseModel()