from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.tools import google_search

from google.cloud import modelarmor_v1
from google.genai import types
from google.api_core.client_options import ClientOptions

import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional


# Load environment variables
load_dotenv(override=True)
GEMINI_MODEL=os.getenv("GEMINI_MODEL")
PROJECT_ID=os.getenv("GOOGLE_CLOUD_PROJECT")
MODEL_ARMOUR_LOCATION=os.getenv("MODEL_ARMOR_LOCATION")
MODEL_ARMOR_TEMPLATE=os.getenv("MODEL_ARMOR_TEMPLATE")

# Initialize Model Armour Client
client = modelarmor_v1.ModelArmorClient(
    transport="rest",
    client_options=ClientOptions(
        api_endpoint=f"modelarmor.{MODEL_ARMOUR_LOCATION}.rep.googleapis.com"
    ),
)

# Parse Model Armour Response function
def parse_model_armor_response(response) -> Optional[str]:
  text2=""
  if response.sanitization_result.filter_match_state.name=="MATCH_FOUND":
    for filter_key, filter_result in response.sanitization_result.filter_results.items():
      if filter_key == "rai":
        if filter_result.rai_filter_result.match_state.name=="MATCH_FOUND":
          for rai_type, rai_details in filter_result.rai_filter_result.rai_filter_type_results.items():
            if rai_details.match_state.name=="MATCH_FOUND":
              text2+=f"{rai_type}\n"
      elif filter_key == "malicious_uris":
          if filter_result.malicious_uri_filter_result.match_state.name == "MATCH_FOUND":
            for item in filter_result.malicious_uri_filter_result.malicious_uri_matched_items:
              text2+=f"URI maliciosa identificada {item.uri}\n"
      elif filter_key == "pi_and_jailbreak":
        if filter_result.pi_and_jailbreak_filter_result.match_state.name=="MATCH_FOUND":
          text2+="Posible Filtración de datos personales o jailbreak\n"
      elif filter_key == "sdp":
        if filter_result.sdp_filter_result.inspect_result.match_state.name=="MATCH_FOUND":
          text2+="Riesgo de filtración de datos sensibles\n"
  return text2 


# Create the prompt and response callbacks to Model Armour
def inspect_prompt(
    callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:

  if llm_request.contents and llm_request.contents[-1].role == 'user':
    if llm_request.contents[-1].parts and llm_request.contents[-1].parts[0].text:
      user_prompt = llm_request.contents[-1].parts[0].text
      user_prompt_data = modelarmor_v1.DataItem(text=user_prompt)

      request = modelarmor_v1.SanitizeUserPromptRequest(
        name=f"projects/{PROJECT_ID}/locations/{MODEL_ARMOUR_LOCATION}/templates/{MODEL_ARMOR_TEMPLATE}",
        user_prompt_data=user_prompt_data,
      )

      response = client.sanitize_user_prompt(request=request)
      text2= parse_model_armor_response(response)
      if text2!="":
        text1="Este prompt ha sido bloqueado por contener elementos no apropiados: "
        part = types.Part.from_text(text=text1+"\n"+text2)
        content = types.Content(parts=[part], role="model")
        return LlmResponse(content=content)
         
  return None


def inspect_response(
    callback_context: CallbackContext, llm_response: LlmResponse
    ) -> Optional[LlmResponse]:

  if llm_response.content and llm_response.content.parts:
    if llm_response.content.parts[0].text:
      model_response = llm_response.content.parts[0].text
      model_response_data = modelarmor_v1.DataItem(text=model_response)
      request = modelarmor_v1.SanitizeModelResponseRequest(
        name=f"projects/{PROJECT_ID}/locations/{MODEL_ARMOUR_LOCATION}/templates/{MODEL_ARMOR_TEMPLATE}",
        model_response_data=model_response_data,
      )
      response = client.sanitize_model_response(request=request)
      text2= parse_model_armor_response(response)
      if text2!="":
        text1="Este prompt ha sido bloqueado por contener elementos no apropiados: "
        part = types.Part.from_text(text=text1+"\n"+text2)
        content = types.Content(parts=[part], role="model")
        return LlmResponse(content=content)
  return None 


# Agent Definition
root_agent = LlmAgent(
    name="GoogleSearchAgent",
    model=os.getenv("GEMINI_MODEL"),
    description="You are an Artificial General Intelligence",
    instruction="Answer any question using your `google_search_tool` as your grounding",
    tools=[google_search],
    before_model_callback=inspect_prompt,
    after_model_callback=inspect_response
)