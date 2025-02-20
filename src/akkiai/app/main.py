from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, Header
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from crew import crew1, crew2, crew3, crew4, crew5, crew6, crew7, crew8, crew9
import helpercodes.kickoff_ids as kickoff_ids
from pathlib import Path
import os 
from datetime import datetime
import secrets
import traceback 
import hmac
import hashlib
import anthropic
from openai import OpenAI
from pytz import timezone 
import uuid
import requests
import crewuserinputs
from diskcache import Cache
from pinecone import Pinecone
from Levenshtein import ratio


app = FastAPI(docs_url=None, redoc_url=None)
url: str = os.environ.get("SUPABASE_URL")
key: str= os.environ.get("SUPABASE_KEY")
supabase: Client= create_client(url, key)
feedback_store={"human_feedback":None}

#for api end point security 
security=HTTPBasic()
DOCS_USERNAME=os.getenv("API_USERNAME1", "default_user")
DOCS_PASSWORD=os.getenv("API_PASSWORD1","default_password")
API_KEY=os.getenv("API_KEY", "apikey")
SECRET_KEY=os.getenv("SECRET_KEY")
ANTHROPIC_API= os.getenv("ANTHROPIC_API_KEY")
DEEPSEEK_API= os.getenv("DEEPSEEK_API_KEY")
ChatGPT_API=os.getenv("GPT_4O_MINI_API_KEY")
GROK_API= os.getenv("GROK_BETA_API_KEY")
LLAMA_3_API_KEY=os.getenv("LLAMA_31_API_KEY")
CACHE_DIR = './prompt_cache_main'  # Cache will be stored in this directory
cache = Cache(CACHE_DIR)
PINECONE_API_KEY= os.getenv("PINECONE_API_KEY")

#Configuration for CORS 

origins=[
    "https://nimble-gnome-f8228f.netlify.app/home",
    "http://localhost:5173",
    "https://api.akki.ai/run",
    "https://beta.akki.ai/",
    "https://beta.akki.ai"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define input models for endpoints
class RunInputs(BaseModel):
    
    SOLUTION_ID: str
    INPUT_1: str
    MODEL_NAME: str
    PROMPT_CACHING_CREW: Optional[str] = Field(default="False", description="Enable or disable prompt caching for the crew.")
    HASH: str

#Chat Endpoint Inputs
class ChatInputs(BaseModel):
    MESSAGE: str
    MODEL_NAME: str
    ENTITY_ID: str
    HASH: str
    
class UpsertInputs(BaseModel):
    MESSAGE: str 
    ENTITY_ID: str
    UPSERT_TYPE: str 
    HASH: str 

class TrainInputs(BaseModel):
    BUSINESS_DETAILS: str
    PRODUCT_DESCRIPTION: str
    n_iterations: int

class TestInputs(BaseModel):
    BUSINESS_DETAILS: str
    PRODUCT_DESCRIPTION: str
    n_iterations: int
    openai_model_name: str

class FeedbackInputs(BaseModel):
    HUMAN_FEEDBACK: str

#Function to authenticate user 
#Authenticate Doc endpoints
async def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, DOCS_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401, detail="Unauthorized", 
            headers={"WWW-Authenticate": "Basic"}
        )

#Function to authenticate api and secrets
async def authenticate_api_key(api_key: str = Header(None)):
    """
    Dependency to authenticate API Key and Secret.
    """
    if not (secrets.compare_digest(api_key or "", API_KEY)):
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid API Key")


async def compute_hash(data: str,secret_key: str) ->str:
     """
     Computes hash with secret key at backend server with data received. Uses Hmac algorithm
     """
     return hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

@app.post("/submit_feedback/", dependencies=[Depends(authenticate_api_key)])
async def submit_feedback(human_feedback:FeedbackInputs):
    '''
    Endpoint to accept human feedback
    '''
    feedback_store["human_feedback"] = human_feedback.HUMAN_FEEDBACK
        
    # Prepare the message to send to Anthropic API
    formatted_feedback = human_feedback.HUMAN_FEEDBACK.strip()
    
    # You can add a system prompt if needed
    system_prompt = "You are a helpful assistant. Process the feedback and determine if changes are necessary."

    # Create the structured messages list for the Anthropic API
    messages = [
        {"role": "user", "content": formatted_feedback}  # Add user feedback as the second message
    ]

    return human_feedback.HUMAN_FEEDBACK


@app.post("/run", dependencies=[Depends(authenticate_api_key)])
async def run(inputs: RunInputs, background_tasks: BackgroundTasks):
    try:
        solution_id=inputs.SOLUTION_ID
        input1=inputs.INPUT_1
        model_name=inputs.MODEL_NAME
        prompt_caching_crew=inputs.PROMPT_CACHING_CREW
        received_hash=inputs.HASH

        crewuserinputs.SharedRunInputs.set_shared_instance(model_name=inputs.MODEL_NAME, prompt_cache=inputs.PROMPT_CACHING_CREW,user_input=inputs.INPUT_1)
         
        #if not (solution_id and input1 and input2 and input3 and received_hash):
        if not (solution_id and input1 and received_hash):
            raise HTTPException(status_code=400, detail="Invalid input data")
        
        #computing hash from received data
        data_string=f"{solution_id}|{input1}"

        #compute hash from data string
        computed_hash= await compute_hash(data_string,SECRET_KEY)

        # Validate the hash
        if not hmac.compare_digest(received_hash, computed_hash):
            raise HTTPException(status_code=401, detail="Unauthorized: Hash does not match")
        
        else: 
            if solution_id == "1":
               akkiai_instance = crew1()

            elif solution_id == "2":
                akkiai_instance = crew2()

            elif solution_id == "3":
                akkiai_instance = crew3()

            elif solution_id == "4":
                akkiai_instance = crew4()
            
            elif solution_id == "5":
                akkiai_instance = crew5()
            
            elif solution_id == "6":
                akkiai_instance = crew6()

            elif solution_id == "7":
                akkiai_instance = crew7()
            
            elif solution_id == "8":
                akkiai_instance = crew8()
            
            elif solution_id == "9":
                akkiai_instance = crew9()

            else:
                return f"Solution id must be 1-9"
            
            crew_instance = akkiai_instance.crew()
            
            if crew_instance is None:
                raise ValueError("Failed to initialize Crew instance.")
            
            # Generate kickoff ID and metadata 
            kickoff_id=crew_instance.id
            kickoff_id=str(kickoff_id)
            kickoff_ids.kickoff_id_temp = str(crew_instance.id)
            print("kickoff id temp is :",kickoff_ids.kickoff_id_temp)
            create_date = datetime.utcnow().isoformat()
            update_date = create_date #what does this mean
            job_status = "on"

            supabase.table("kickoff_details").insert({"kickoff_id": kickoff_id, "job_status": job_status, "create_date":create_date, "update_date":update_date, "model_name":model_name}).execute()
            
            background_tasks.add_task(run_crew_bg, crew_instance, inputs, solution_id, kickoff_id)
            
            return {"kickoff_id": kickoff_id}
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Exception in /run: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error running crew: {str(e)}. Traceback: {error_details}")
    
async def generate_cache_input(user_input):
    """
    Cache the user input for prompt caching
    """
    try:
        cache_key= hashlib.md5(user_input.encode()).hexdigest()
        return cache_key
    except Exception as e:
        print(f"Error caching input: {e}")


async def run_crew_bg(crew_instance, inputs, solution_id, kickoff_id ):
    try: 
        cache_key= await generate_cache_input(inputs.INPUT_1)
        """
        fetching the cached input.
        """
        if cache_key in cache:
            print("retrieving input from cache")
            cached_input= cache[cache_key]
            user_input=cached_input
        else: 
            user_input=inputs.INPUT_1

        if solution_id == "1":
            # Pass the inputs to the backend agent (replace with your actual logic)
            result = await crew_instance.kickoff_async(inputs={
                "STARTUP_INFO": user_input,
            })

        elif solution_id == "2":
             # Pass the inputs to the backend agent (replace with your actual logic)
            result = await crew_instance.kickoff_async(inputs={
                "STARTUP_INFO": user_input,
            })

        elif solution_id == "3":

            result = await crew_instance.kickoff_async(inputs={
                "STARTUP_INFO":user_input,
            })
        
        elif solution_id == "4":
              # Pass the inputs to the backend agent (replace with your actual logic)
            result = await crew_instance.kickoff_async(inputs={
                "STARTUP_INFO":user_input,
            })

        elif solution_id == "5":
            # Pass the inputs to the backend agent (replace with your actual logic)
            result = await crew_instance.kickoff_async(inputs={
                "STARTUP_INFO": user_input,
            })
        elif solution_id == "6":
            # Pass the inputs to the backend agent (replace with your actual logic)
            result = await crew_instance.kickoff_async(inputs={
                "STARTUP_INFO":user_input,
            })
        elif solution_id == "7":
            result = await crew_instance.kickoff_async(inputs={
                "STARTUP_INFO": user_input,
            })
        elif solution_id == "8":
            result = await crew_instance.kickoff_async(inputs={
                "STARTUP_INFO": user_input,
            })
        elif solution_id == "9":
            result = await crew_instance.kickoff_async(inputs={
                "STARTUP_INFO": user_input,
            })
        
        job_status = "off"
        update_date =  datetime.utcnow().isoformat()
        supabase.table("kickoff_details").update({'job_status':job_status, 'update_date':update_date}).eq("kickoff_id",kickoff_ids.kickoff_id_temp).execute()
   
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Exception in run_kickoff: {error_details}")


"""
CHAT ENDPOINT AHEAD
"""

class ConversationHistory:
    def __init__(self):
        #initialising empty list to store conversation 
        self.turns = []
    
    #storing response of assitant 
    def update_assistant_turn(self, content):
        self.turns.append(
            {
                "role":"assistant",
                "content": [
                    {
                        "type":"text",
                        "text": content 
                    }
                ]
            }
        )

    #storing user text to turns
    def update_user_turn(self, content):
        self.turns.append(
            {
                "role":"user",
                "content": [
                    {
                        "type":"text",
                        "text": content
                    }
                ]
            }
        )
    #retrive the conversations in past turns
    def get_turns(self):
        # Retrieve conversation turns with specific formatting
        result = []
        user_turns_processed = 0
        # Iterate through turns in reverse order
        for turn in reversed(self.turns):
            if turn["role"] == "user" and user_turns_processed < 3:
                # Add the last user turn with ephemeral cache control
                result.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": turn["content"][0]["text"],
                            "cache_control": {"type": "ephemeral"}
                        }
                    ]
                })
                user_turns_processed += 1
            else:
                # Add other turns as they are
                result.append(turn)
        # Return the turns in the original order
        return list(reversed(result))
    
conversation_history= ConversationHistory()

async def upsert_pc_data(pc,index,entity_id, message_id, user_input, llm_response):

    """
    Upserting the past conversation of each user with namespaces for Long term memory.
    """

    #upserting data into index with namespaces
    embeddings = pc.inference.embed(
    model="multilingual-e5-large",
    inputs=[user_input],
    parameters={"input_type": "passage", "truncate": "END"}
    )

    vectors = []
    for d, e in zip([user_input], embeddings):
        vectors.append({
            "id": message_id,
            "values": e['values'],
            "metadata": {"user_text":user_input, "llm-response":llm_response}
        })

    index.upsert(
        vectors=vectors,
        namespace=entity_id
    )


async def update_perm_kb(pc,message_id,entity_id, perm_kb):
    """
    Updating the Permanent knowledge base with the new conversation details.
    """
    perm_kb_to_be_upserted= perm_kb
    index=pc.Index(host="https://permanent-kb-py172ny.svc.aped-4627-b74a.pinecone.io")

    embeddings= pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[perm_kb],
        parameters={"input_type": "passage", "truncate": "END"}
    ) 

    "Checking if a data already exists in the RAG and Upserting only if it doesn't exist"

    update_data_embeddings= pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[perm_kb],
        parameters={"input_type": "passage", "truncate": "END"}
    )
    retrived_data= await get_perm_kb_RAG(pc,entity_id,update_data_embeddings[0].values, k=1)
    retrieved_perm_kb=[]
    for match in retrived_data.get('matches',[]):
        metadata=match.get('metadata',{})
        if metadata:
            retrieved_perm_kb.append(metadata.get('perm_kb', '').strip())
        else:
            retrieved_perm_kb="Nil"

    perm_kb_retrived="\n\n".join(retrieved_perm_kb)

    threshold=0.8
    similarity = ratio(perm_kb_retrived, perm_kb_to_be_upserted)  # Returns a similarity score between 0 and 1
    if (similarity <= threshold):
        """
        Only upsert the data if the perm_kb_to_be_upserted is less than 80% similar to perm_kb_retrived
        """

        vectors=[]
        for d, e in zip([perm_kb], embeddings):
            vectors.append({
                "id": message_id,
                "values": e['values'],
                "metadata": {"perm_kb": perm_kb}
            })

        index.upsert(
            vectors=vectors,
            namespace=entity_id
        )

async def update_temp_kb(pc,message_id, entity_id, temp_kb):
    """
    Updating the temporary knowledge base with the new conversation details.
    """
    temp_kb_to_be_upserted= temp_kb
    index=pc.Index(host="https://temporary-kb-py172ny.svc.aped-4627-b74a.pinecone.io")

    embeddings= pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[temp_kb],
        parameters={"input_type": "passage", "truncate": "END"}
    ) 

    "Checking if a data already exists in the RAG and not pushing it then"

    data_to_be_upserted_embeddings= pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[temp_kb],
        parameters={"input_type": "passage", "truncate": "END"}
    )
    retrived_data= await get_temp_kb_RAG(pc,entity_id,data_to_be_upserted_embeddings[0].values, k=1)

    retrived_temp_kb=[]
    for match in retrived_data.get('matches',[]):
        metadata=match.get('metadata',{})
        if metadata:
            retrived_temp_kb.append(metadata.get('temp_kb', '').strip())
        else:
            retrived_temp_kb="Nil"

    temp_kb_retrived="\n\n".join(retrived_temp_kb)

    threshold=0.8
    similarity = ratio(temp_kb_retrived, temp_kb_to_be_upserted)  # Returns a similarity score between 0 and 1
    if (similarity <= threshold):
        """
        Only upsert the data if the character_to_be_upserted is less than 80% similar to character_retrived
        """
        vectors=[]
        for d, e in zip([temp_kb], embeddings):
            vectors.append({
                "id": message_id,
                "values": e['values'],
                "metadata": {"temp_kb": temp_kb}
            })

        index.upsert(
            vectors=vectors,
            namespace=entity_id
        )

async def update_character_kb(pc,message_id, entity_id, character):
    """
    Updating the character knowledge base with the new conversation details.
    """
    character_to_be_upserted=character
    index=pc.Index(host="https://character-kb-py172ny.svc.aped-4627-b74a.pinecone.io")
    embeddings= pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[character],
        parameters={"input_type": "passage", "truncate": "END"}
    ) 

    "Checking if a data already exists in the RAG and not pushing it then"

    update_data_embeddings= pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[character],
        parameters={"input_type": "passage", "truncate": "END"}
    )
    retrived_data= await get_character_RAG(pc,entity_id,update_data_embeddings[0].values, k=1)
    retrieved_character=[]
    for match in retrived_data.get('matches',[]):
        metadata=match.get('metadata',{})
        if metadata:
            retrieved_character.append(metadata.get('character', '').strip())
        else:
            retrieved_character="Nil"

    character_retrieved="\n\n".join(retrieved_character)

    threshold=0.8
    similarity = ratio(character_retrieved, character_to_be_upserted)  # Returns a similarity score between 0 and 1
    if (similarity <= threshold):
        """
        Only upsert the data if the character_to_be_upserted is less than 80% similar to character_retrived
        """

        vectors=[]
        for d, e in zip([character], embeddings):
            vectors.append({
                "id": message_id,
                "values": e['values'],
                "metadata": {"character": character}
            })

        index.upsert(
            vectors=vectors,
            namespace=entity_id
        )

async def get_perm_kb_RAG(pc,entity_id, vector, k=3):
    index=pc.Index(host="https://permanent-kb-py172ny.svc.aped-4627-b74a.pinecone.io")
    result=index.query(
        namespace=entity_id,
        vector=vector,
        top_k=k,
        include_values=False,
        include_metadata=True
    )
    return result

async def get_temp_kb_RAG(pc,entity_id, vector, k=3):
    index=pc.Index(host="https://temporary-kb-py172ny.svc.aped-4627-b74a.pinecone.io")
    result=index.query(
        namespace=entity_id,
        vector=vector,
        top_k=k,
        include_values=False,
        include_metadata=True
    )
    return result    

async def get_character_RAG(pc,entity_id, vector, k=3):
    index=pc.Index(host="https://character-kb-py172ny.svc.aped-4627-b74a.pinecone.io")
    result=index.query(
        namespace=entity_id,
        vector=vector,
        top_k=k,
        include_values=False,
        include_metadata=True
    )
    return result 


async def push_retrived_data_to_db(job_id,perm_kb,temp_kb,character,context_string):
    supabase_key: str= os.environ.get("SUPABASE_KEY")
    supabase: Client= create_client(url, supabase_key)
    supabase.table("retrieved_chat_rag").insert({'job_id':job_id,'perm_kb':perm_kb, 'temp_kb':temp_kb,'character':character, "conversation_context":context_string}).execute()

#running all the chats simultaneously in the background
async def chat_bg(input,input_message, kickoff_id,create_date, API_NAME):
    
    pc=Pinecone(api_key=PINECONE_API_KEY)
    index=pc.Index(host="https://akkiai-chat-py172ny.svc.aped-4627-b74a.pinecone.io")
    #generating embedding of the user input 
    entity_id=input.ENTITY_ID

    input_embeddings= pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[input.MESSAGE],
        parameters={"input_type": "passage", "truncate": "END"}
    )

    result=index.query(
        namespace=entity_id,
        vector=input_embeddings[0].values,
        top_k=1,
        include_values=False,
        include_metadata=True
    )
    
    """
    Retriveing Permanent Temperory and Character Knowledge of the Entity
    """

    result_perm_kb= await get_perm_kb_RAG(pc,entity_id, input_embeddings[0].values, k=1)
    result_temp_kb= await get_temp_kb_RAG(pc,entity_id, input_embeddings[0].values, k=1)
    result_character= await get_character_RAG(pc,entity_id,input_embeddings[0].values, k=1)
    

    retrieved_contexts = []
    for match in result.get('matches', []):
        metadata = match.get('metadata',{})
        if metadata:
            user_text = metadata.get('user_text', '').strip()
            llm_response = metadata.get('llm-response', '').strip()
            retrieved_contexts.append(f"User: {user_text}\nAssistant: {llm_response}")
        else:
            retrieved_contexts="Nil"
    
    context_string = "\n\n".join(retrieved_contexts)

    retrieved_perm_kb=[]
    retrieved_temp_kb=[]
    retrieved_character=[]

    for match in result_perm_kb.get('matches', []):
        metadata = match.get('metadata', {})
        if metadata:
            retrieved_perm_kb.append(metadata.get('perm_kb', '').strip())
        else:
            retrieved_perm_kb="Nil"

    perm_kb="\n\n".join(retrieved_perm_kb)

    for match in result_temp_kb.get('matches', []):
        metadata = match.get('metadata', {})
        if metadata:
            retrieved_temp_kb.append(metadata.get('temp_kb', '').strip())
        else:
            retrieved_temp_kb="Nil"
        
    temp_kb="\n\n".join(retrieved_temp_kb)

    for match in result_character.get('matches',[]):
        metadata=match.get('metadata',{})
        if metadata:
            retrieved_character.append(metadata.get('character', '').strip())
        else:
            retrieved_character="Nil"

    character="\n\n".join(retrieved_character)

    system_prompt = f"""
        You are a highly specialized and empathetic assistant with deep expertise in tailoring your responses to individual users. Your role is to provide accurate, insightful, and personalized advice by taking into account the user's long-term background, current focus, personality traits, and past conversation context.

        Below is the detailed profile of the user:
        -------------------------------------------------
        Permanent Knowledge:
        {perm_kb}

        Temporary Knowledge:
        {temp_kb}

        Character Profile:
        {character}

        Recent Conversation Context:
        {context_string}
        -------------------------------------------------

        When responding to the user's queries, please ensure that:
        - You incorporate relevant details from the permanent knowledge to reflect the user's long-term expertise and interests.
        - You factor in the temporary knowledge to address the user's current focus and immediate concerns.
        - You adjust your tone and style according to the character profile, ensuring that your response is empathetic, thoughtful, and aligned with the user's personality.
        - You leverage the conversation context to maintain continuity and coherence in your responses, ensuring that previous discussions are respected and built upon.

        Your answer should be precise, well-organized, and directly address the user's query while remaining deeply personalized and context-aware.
        """
    print(system_prompt)
    if API_NAME=="claude-3-haiku-20240307":        
        #conversation_history.update_user_turn(input.MESSAGE)
        client= anthropic.Anthropic(api_key=ANTHROPIC_API)
        MODEL_NAME="claude-3-haiku-20240307"
        system_message = system_prompt

        completion = client.messages.create(
                    model=MODEL_NAME,
                    max_tokens=1024,
                    extra_headers={
                        "anthropic-beta":"prompt-caching-2024-07-31"
                    },
                    system=[
                        {"type": "text", "text": system_message,"cache_control": {"type": "ephemeral"}},
                        ],
                    #messages=conversation_history.get_turns(),
                    messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": input.MESSAGE,
                            "cache_control": {"type": "ephemeral"}
                        }
                    ]
                }]
                )
        
        message_id= completion.id
        response= completion.content[0].text
        task_name= completion.model
        conversation_history.update_assistant_turn(response)

    elif API_NAME=="deepseek-chat":
        system_message = system_prompt
        conversation_history.update_user_turn(input.MESSAGE)
        client= OpenAI(api_key=DEEPSEEK_API, base_url="https://api.deepseek.com")
        completion=client.chat.completions.create(
            model="deepseek-chat",
            #messages=conversation_history.get_turns() + [{"role":"system","content":system_message}]
            messages=[input.MESSAGE] + [{"role":"system","content":system_message}]
        )
        response= completion.choices[0].message.content
        message_id=completion.id
        task_name=completion.model 
        conversation_history.update_assistant_turn(response)

    elif API_NAME=="gpt-4o-mini":
            
            conversation_history.update_user_turn(input.MESSAGE)
            client= OpenAI(api_key=ChatGPT_API)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                #messages= conversation_history.get_turns() + [{"role":"system","content":system_prompt}]
                messages=[input.MESSAGE] + [{"role":"system","content":system_message}]
            )
            response= completion.choices[0].message.content
            message_id=completion.id
            task_name=completion.model
            conversation_history.update_assistant_turn(response)

    elif API_NAME=="grok-beta":
          conversation_history.update_user_turn(input.MESSAGE)
          client= OpenAI(api_key=GROK_API, base_url="https://api.x.ai/v1")
          completion = client.chat.completions.create(
                model="gpt-4o-mini",
                #messages=conversation_history.get_turns() + [{"role":"system","content":system_prompt}]
                messages=[input.MESSAGE] + [{"role":"system","content":system_message}]
            )
          response= completion.choices[0].message.content
          message_id=completion.id
          task_name=completion.model
          conversation_history.update_assistant_turn(response) 

    elif API_NAME=="llama3.1-70b":
        conversation_history.update_user_turn(input.MESSAGE)
        client= OpenAI(api_key=LLAMA_3_API_KEY, base_url="https://api.llama-api.com")
        completion = client.chat.completions.create(
                model="llama3.1-70b",
                #messages=conversation_history.get_turns() + [{"role":"system","content":system_prompt}]
                messages=[input.MESSAGE] + [{"role":"system","content":system_message}]
            )
        response= completion.choices[0].message.content
        message_id=str(uuid.uuid4())
        task_name=completion.model 
        completion.id=message_id
        conversation_history.update_assistant_turn(response)

    message_id=completion.id
    task_name=completion.model
    """
    Push the message id and the anthropic response to the SUPABASE db
    kickoff_id column --> message_id
    task_name column ---> the model that is being used here Haiku 3
    task_input column --> the input provided by the user
    
    """
    update_date= datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S.%f')
    job_status="off"
    job_id= str(uuid.uuid4())
    supabase.table("kickoff_details").update({'kickoff_id':message_id,'job_status':job_status, 'update_date':update_date,}).eq("create_date",create_date).execute()
    supabase.table("run_details").insert({"kickoff_id": message_id,'task_name':task_name,'job_id':job_id, 'input':input_message,'output':response}).execute()
    
    """
    Pushing RAG contexts to DB
    """

    await push_retrived_data_to_db(job_id,perm_kb,temp_kb,character,context_string)
    
    webhook_url =os.environ.get("WEBHOOK_URL")
    return response
    """
    NO need to send Webhook call for Chat Endpoint - Rashmi 14th Feb 
    """        
    try:
        response=requests.post(
            webhook_url,
            json={
                "kickoff_id": message_id,
                "task_name": task_name,
                "task_output": response #This will now send strings
            },
            timeout=10
            )
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        # Log the success
        print(f"Webhook sent successfully: {response.status_code}, {response.json()}")

    except requests.exceptions.RequestException as e:
        # Log any errors during the webhook call
        print(f"Error sending webhook: {str(e)}")

#Chat endpoint for AkkiAI
@app.post("/chat", dependencies= [Depends(authenticate_api_key)])
async def chat(input: ChatInputs, background_tasks: BackgroundTasks):
    try:
        input_message=input.MESSAGE
        received_hash= input.HASH
        model_name= input.MODEL_NAME

        #if not (input_message and received_hash):
            #raise HTTPException(status_code=400, detail="Invalid input data")
        
        data_string=f"{input_message}|{model_name}"
        #compute hash from data string
        computed_hash= await compute_hash(data_string,SECRET_KEY)

        # Validate the hash
        #if not hmac.compare_digest(received_hash, computed_hash):
            #raise HTTPException(status_code=401, detail="Unauthorized: Hash does not match")
        #else:
        # 
        """
        For hashless test of deployment
        """
        if 1<4: 
            if not ANTHROPIC_API:
                raise ValueError("ANTHROPIC_API environment variable not found. Please set it with your API key.")

 
            """
            Pushing the data into Kickoff_id table
            """
            create_date = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S.%f')
            update_date = create_date #what does this mean
            job_status = "on"
            kickoff_id= str(uuid.uuid4())
           

            supabase.table("kickoff_details").insert({"kickoff_id": kickoff_id, "job_status": job_status, "create_date":create_date, "update_date":update_date}).execute()
            #background_tasks.add_task(chat_bg,input,input_message,kickoff_id,create_date,model_name)
            response= await chat_bg(input,input_message,kickoff_id,create_date,model_name)

            return {'response':response}
     
            #return {"The Chat has been submitted. Message ID:": kickoff_id}
        
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


"""
/UPSERT endpoint to push data to Temp_KB, Perm_KB or Character KB
"""
@app.post("/upsert", dependencies= [Depends(authenticate_api_key)])
async def upsert(inputs: UpsertInputs, background_tasks: BackgroundTasks):
    try:
        data= inputs.MESSAGE
        entity_id= inputs.ENTITY_ID
        upsert_type=inputs.UPSERT_TYPE
        received_hash=inputs.HASH
        message_id= str(uuid.uuid4())

        data_string=f"{data}|{entity_id}|{upsert_type}"

        #compute hash from data string
        computed_hash= await compute_hash(data_string,SECRET_KEY)

        # Validate the hash
        #if not hmac.compare_digest(received_hash, computed_hash):
            #raise HTTPException(status_code=401, detail="Unauthorized: Hash does not match")
    
        #else: 
        """
        For hashless test of deployment
        """
        if 1<4:

            pc=Pinecone(api_key=PINECONE_API_KEY)

            if upsert_type == "perm_kb":
              await update_perm_kb(pc, message_id, entity_id, data)
            elif upsert_type == "temp_kb":
                await update_temp_kb(pc, message_id, entity_id, data)
            elif upsert_type == "character":
                await update_character_kb(pc, message_id, entity_id, data)
            elif upsert_type == "conversation_history":
                await upsert_pc_data(pc, entity_id, user_input=data, llm_response="NIL")
            else:
               raise HTTPException(status_code=400, detail="Invalid upsert type")
            
            return {"response": f"Upsert to {upsert_type} successful"}
        
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/train", dependencies=[Depends(authenticate_api_key)])
async def train(inputs: TrainInputs):
    try:
        crew1().crew().train(
            n_iterations=inputs.n_iterations,
            filename=inputs.filename,
            inputs={"BUSINESS_DETAILS": inputs.BUSINESS_DETAILS, "PRODUCT_DESCRIPTION": inputs.PRODUCT_DESCRIPTION},
        )
        return {"message": "Training completed successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training crew: {str(e)}")

@app.post("/replay", dependencies=[Depends(authenticate_api_key)])
async def replay(task_id: str):
      try:
        crew1().crew().replay(task_id=task_id)
        return {"message": "Replay executed successfully!"}
      except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error replaying crew: {str(e)}")

@app.post("/test", dependencies=[Depends(authenticate_api_key)])
async def test(inputs: TestInputs):
    try:
        crew1().crew().test(
            n_iterations=inputs.n_iterations,
            openai_model_name=inputs.openai_model_name,
            inputs={"BUSINESS_DETAILS": inputs.BUSINESS_DETAILS, "PRODUCT_DESCRIPTION": inputs.PRODUCT_DESCRIPTION},
        )
        return {"message": "Test executed successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing crew: {str(e)}")
    
@app.get("/", dependencies=[Depends(authenticate)])
async def root():
    return {"message": "Welcome to the CrewAI API!"}

@app.get("/{username}/{password}")
async def solution_page(username: str, password: str):
    if username == DOCS_USERNAME and password == DOCS_PASSWORD:
        return {"message": "Access granted to the solution page"}
    raise HTTPException(
        status_code=401, detail="Unauthorized access"
    )

@app.get("/docs", dependencies=[Depends(authenticate)])
async def fastapi_docs():
    """
    Custom route for /docs to protect it with authentication.
    """
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="AkkiAI Multi Agents"
    )
@app.get("/redoc", dependencies=[Depends(authenticate)])
async def custom_redoc():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title="Secure API Docs")